#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-10-03
#

"""
Manage email clients and their settings
"""

from __future__ import print_function, unicode_literals, absolute_import

from email.header import Header
from fnmatch import fnmatch
import os
import re
from time import time
from urllib import quote

from workflow.background import run_in_background, is_running

from common import ONE_DAY, appname, bundleid
import verbose_json as json

log = None

match_bundle_id = re.compile(r'kMDItemCFBundleIdentifier = "(.+)"').match


MAX_APP_CACHE_AGE = ONE_DAY


# Client-specific formatting rules
# `True` means use the feature, `False` means don't use the feature
# spaces    = delimit recipients with `, `, not just `,`
# names     = also include recipient names in the mailto: URI.
#             If `False`, names will never be sent. Of the tested clients,
#             only Airmail chokes on names, but it's smart enough to retrive
#             the name from your Contacts.app database
# mime      = MIME-encode non-ASCII characters in names. No known client
#             requires this. If encoded, the recipient will also be
#             URL-quoted
# no_commas = Client chokes on commas in a recipient's name. For most
#             clients, it's sufficient to enclose such names in ""
# inline_to = Client requires URI of form `mailto:email.address@domain.com`
#             not `mailto:?to=email.address@domain.com`. Airmail and
#             Mailbox (Beta) disagree here. No other client cares.

DEFAULT_RULES = {
    "spaces": True,
    "names": True,
    "mime": True,
    "no_commas": False,
    "inline_to": False
}

# Client-specific rules are loaded from the `client_rules.json` file
# adjacent to this file and the file of the same name in the workflow's
# data directory (if it exists and contains anything).
# The file in the data directory overrides the default one.


# oooooooooooo                                                    .       .
# `888'     `8                                                  .o8     .o8
#  888          .ooooo.  oooo d8b ooo. .oo.  .oo.    .oooo.   .o888oo .o888oo  .ooooo.  oooo d8b
#  888oooo8    d88' `88b `888""8P `888P"Y88bP"Y88b  `P  )88b    888     888   d88' `88b `888""8P
#  888    "    888   888  888      888   888   888   .oP"888    888     888   888ooo888  888
#  888         888   888  888      888   888   888  d8(  888    888 .   888 . 888    .o  888
# o888o        `Y8bod8P' d888b    o888o o888o o888o `Y888""8o   "888"   "888" `Y8bod8P' d888b


class Formatter(object):
    """Format the mailto: URL according to client-specific rules

    See `RULES` for details.

    """

    def __init__(self, client, wf):
        global log
        self.client = client
        self.wf = wf
        log = self.wf.logger
        # Load rules
        client_rules = {}
        for path in [self.wf.workflowfile('client_rules.json'),
                     self.wf.datafile('client_rules.json')]:
            if not os.path.exists(path):
                continue
            log.debug(
                'Loading client formatting rules from {} ...'.format(path))
            with open(path) as fp:
                client_rules.update(json.load(fp))
        self.rules = DEFAULT_RULES
        # Get rules for selected client
        for bundle_id in client_rules:
            if fnmatch(client, bundle_id):
                self.rules = client_rules.get(bundle_id)
                break

        for key in ('spaces', 'names', 'mime', 'no_commas', 'inline_to'):
            value = self.rules[key]
            setattr(self, 'use_{}'.format(key), value)

        log.debug(u'Loaded rules {!r} for client {!r}'.format(self.rules,
                                                              client))

    def get_url(self, contacts, use_names=False):
        """Return formatted unicode URL for contacts

        :param contacts: list of 2-tuples: (name, email)
        :returns: string (bytes)
        """
        log.debug(u"Building URL for app '{}'".format(self.client))
        parts = []
        encoded = False
        for contact in contacts:
            name, email = contact
            if not self.use_names or not use_names:
                parts.append(email)
                log.debug('[not use_names] {!r} --> {!r}'.format(contact,
                                                                 email))
                continue

            elif name is None:  # email addy not in Address Book
                parts.append(email)
                log.debug('[name not found] {!r} --> {!r}'.format(contact,
                                                                  email))
                continue

            if self.use_mime:
                try:
                    name = name.encode('ascii')
                except UnicodeEncodeError:
                    name = str(Header(name, 'utf-8'))
                    encoded = True

            if ',' in name:
                if self.use_no_commas:
                    parts.append(email)
                    log.debug('[use_no_commas] {!r} --> {!r}'.format(contact,
                                                                     email))
                    continue

                else:
                    name = '"{}"'.format(name)

            addr = '{} <{}>'.format(name, email)
            log.debug('[default] {!r} --> {!r}'.format(contact, addr))
            parts.append(addr)

        if self.use_spaces:
            result = ', '.join(parts)
        else:
            result = ','.join(parts)

        result = result.encode('utf-8')

        if encoded:  # also needs quoting
            result = quote(result, safe='@')
        if self.use_inline_to:
            return b'mailto:{}'.format(result)
        return b'mailto:?to={}'.format(result)


#   .oooooo.   oooo   o8o                            .
#  d8P'  `Y8b  `888   `"'                          .o8
# 888           888  oooo   .ooooo.  ooo. .oo.   .o888oo
# 888           888  `888  d88' `88b `888P"Y88b    888
# 888           888   888  888ooo888  888   888    888
# `88b    ooo   888   888  888    .o  888   888    888 .
#  `Y8bood8P'  o888o o888o `Y8bod8P' o888o o888o   "888"

class Client(object):
    """Email client manager

    Maintains a list of all email clients on the system, which is the
    system default and which is the default for MailTo (if one is set)
    """

    def __init__(self, wf):
        global log
        self.wf = wf
        log = wf.logger
        self.all_email_apps = []
        self.system_default_app = {}
        self.update()

    def get_default_app(self):
        """Return info dict on default email client or None

        {'name': 'Application Name', 'path': '/path/to/Application.app',
         'bundleid': 'com.application.bundleid'}

        """

        # return self.wf.settings.get('default_app') or self.system_default_app()

        return self.wf.settings.get('default_app') or self.system_default_app

    def set_default_app(self, app_path):
        """Set default email client to application at ``app_path``"""
        d = {'path': app_path}
        d['name'] = appname(app_path)
        d['bundleid'] = bundleid(app_path)
        self.wf.settings['default_app'] = d
        # wf.settings.save()
        log.debug('Set default app to : %r', d)

    default_app = property(get_default_app, set_default_app)

    def build_url(self, emails):
        """Return mailto: URL built with appropriate formatter"""
        contacts = self.wf.cached_data('contacts', max_age=0)

        if not contacts:
            raise ValueError('No contacts available')

        email_name_map = contacts['email_name_map']

        # [(name, email), ...]
        recipients = [(email_name_map.get(email), email) for
                      email in emails]

        app = self.default_app

        bundleid = None
        if isinstance(app, dict):
            bundleid = app['bundleid']
        elif isinstance(app, basestring):
            bundleid = app

        formatter = Formatter(bundleid, self.wf)
        return formatter.get_url(recipients,
                                 self.wf.settings.get('use_name', True))

    def update(self, force=False):
        """Load apps from cache, update if required"""
        self.all_email_apps = self.wf.cached_data('all_apps', max_age=0)
        self.system_default_app = self.wf.cached_data('system_default_app',
                                                      max_age=0)
        if self.all_email_apps is None:
            self.all_email_apps = []
        if self.system_default_app is None:
            self.system_default_app = {}

        do_update = False
        if force:
            do_update = True
        elif not self.wf.cached_data_fresh('all_apps', MAX_APP_CACHE_AGE):
            do_update = True
        elif not self.wf.cached_data_fresh('system_default_app',
                                           MAX_APP_CACHE_AGE):
            do_update = True
        # Update if required
        if do_update:
            log.debug('Updating application caches ...')
            cmd = ['/usr/bin/python', self.wf.workflowfile('update_apps.py')]
            run_in_background('update-apps', cmd)

    @property
    def updating(self):
        return is_running('update-apps')

    @property
    def empty(self):
        return not self.all_email_apps or not self.system_default_app


if __name__ == '__main__':
    from workflow import Workflow
    wf = Workflow()

    def timeit(func, *args, **kwargs):
        s = time()
        func(*args, **kwargs)
        d = time() - s
        log.debug('{} run in {:0.3f} seconds'.format(func.__name__, d))

    c = Client(wf)
    wf.reset()
    log.info('First run')
    timeit(c.update)
    timeit(c.get_default_app)
    log.info('Second run')
    timeit(c.update)
    timeit(c.get_default_app)
    print('Default app : {}'.format(c.get_default_app()))
