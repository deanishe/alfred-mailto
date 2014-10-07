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
import os
import re
from time import time
from urllib import quote, unquote
from urlparse import urlparse

from workflow import Workflow

from common import command_output, ONE_DAY

wf = Workflow()
log = wf.logger

match_bundle_id = re.compile(r'kMDItemCFBundleIdentifier = "(.+)"').match


MAX_APP_CACHE_AGE = ONE_DAY


# Client-specific formatting rules
#               spaces, names, MIME, no commas
DEFAULT_RULES = (True, True, True, False)


RULES = {
    u'it.bloop.airmail': (False, False, False, False),
    u'com.eightloops.Unibox': (True, True, False, True),
    u'com.google.Chrome': (True, True, False, False),
    u'com.freron.MailMate': (True, True, False, False),
    u'com.dropbox.mbd.external-beta': (False, False, False, False)
}

# Where to search for applications
APPLICATION_PATHS = ('/Applications', os.path.expanduser('~/Applications'))


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

    def __init__(self, client):
        self.client = client
        self.rules = RULES.get(client, DEFAULT_RULES)
        (self.use_spaces,
         self.use_names,
         self.use_mime,
         self.use_no_commas) = self.rules
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
        return b'mailto:{}'.format(result)


#   .oooooo.   oooo   o8o                            .
#  d8P'  `Y8b  `888   `"'                          .o8
# 888           888  oooo   .ooooo.  ooo. .oo.   .o888oo
# 888           888  `888  d88' `88b `888P"Y88b    888
# 888           888   888  888ooo888  888   888    888
# `88b    ooo   888   888  888    .o  888   888    888 .
#  `Y8bood8P'  o888o o888o `Y8bod8P' o888o o888o   "888"

class Client(object):
    """Email client manager"""

    def __init__(self):
        pass

    def get_default_app(self):
        """Return info dict on default email client or None

        {'name': 'Application Name', 'path': '/path/to/Application.app',
         'bundleid': 'com.application.bundleid'}

        """

        # return wf.settings.get('default_app') or self.system_default_app()

        return wf.settings.get('default_app') or self.system_default_app

    def set_default_app(self, app_path):
        """Set default email client to application at ``app_path``"""
        d = {'path': app_path}
        d['name'] = self.appname(app_path)
        d['bundleid'] = self.bundleid(app_path)
        wf.settings['default_app'] = d

    default_app = property(get_default_app, set_default_app)

    def build_url(self, emails):
        """Return mailto: URL built with appropriate formatter"""
        contacts = wf.cached_data('contacts', max_age=0)

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

        formatter = Formatter(bundleid)
        return formatter.get_url(recipients, wf.settings.get('use_name', True))

    def update(self):
        """Force update of system default app and list of mailto handlers"""
        log.debug('Updating application caches ...')
        self.get_all_email_apps(force=True)
        self.get_system_default_app(force=True)

    # dP     dP           dP
    # 88     88           88
    # 88aaaaa88a .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
    # 88     88  88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
    # 88     88  88.  ... 88 88.  .88 88.  ... 88             88
    # dP     dP  `88888P' dP 88Y888P' `88888P' dP       `88888P'
    #                        88
    #                        dP

    def get_all_email_apps(self, force=False):
        """Return list of all applications that support mailto:

        [('app name', '/app/path'), ...]

        """
        if force:
            wf.cache_data('all_apps', None)
        return wf.cached_data('all_apps',
                              self._find_email_handlers,
                              MAX_APP_CACHE_AGE)

    all_email_apps = property(get_all_email_apps)

    def get_system_default_app(self, force=False):
        """Return bundleid of system default email client"""
        if force:
            wf.cache_data('system_default_app', None)
        return wf.cached_data('system_default_app',
                              self._find_system_default_handler,
                              MAX_APP_CACHE_AGE)

    system_default_app = property(get_system_default_app)

    def appname(self, app_path):
        """Return app name for application at ``app_path``"""
        return os.path.splitext(os.path.basename(app_path))[0]

    def bundleid(self, app_path):
        """Return bundle ID for application at ``app_path``"""
        cmd = ['mdls', '-name', 'kMDItemCFBundleIdentifier', app_path]
        output = command_output(cmd)

        m = match_bundle_id(output)

        if not m:
            raise ValueError(
                'No bundle ID found for application `{}`'.format(app_path))

        return m.group(1)

    def _find_email_handlers(self):
        """Find all apps that can handle mailto URLs"""
        from LaunchServices import (LSCopyApplicationURLsForURL,
                                    kLSRolesAll,
                                    CFURLCreateWithString)

        url = CFURLCreateWithString(None, 'mailto:test@example.com', None)
        apps = set()

        nsurls = LSCopyApplicationURLsForURL(url, kLSRolesAll)
        paths = set([self._nsurl_to_path(nsurl) for nsurl in nsurls])

        for path in paths:
            apps.add((self.appname(path), path))
            log.debug('mailto handler : {}'.format(
                      path))

        apps = sorted(apps)

        log.debug('{} email clients found'.format(len(apps)))

        return apps

    def _find_system_default_handler(self):
        """Return app info for system default mailto handler"""
        from LaunchServices import (LSGetApplicationForURL,
                                    kLSRolesAll,
                                    CFURLCreateWithString)
        url = CFURLCreateWithString(None, 'mailto:test@example.com', None)
        app = {}
        ok, info, nsurl = LSGetApplicationForURL(url, kLSRolesAll,
                                                 None, None)

        app['path'] = self._nsurl_to_path(nsurl)
        app['name'] = self.appname(app['path'])
        app['bundleid'] = self.bundleid(app['path'])

        log.debug('System default mailto handler : {}'.format(app))
        return app

    def _nsurl_to_path(self, nsurl):
        """Convert a file:// NSURL object to a Unicode path"""
        return wf.decode(nsurl.path()).rstrip('/')


if __name__ == '__main__':
    def timeit(func, *args, **kwargs):
        s = time()
        func(*args, **kwargs)
        d = time() - s
        log.debug('{} run in {:0.3f} seconds'.format(func.__name__, d))
    c = Client()
    wf.reset()
    log.info('First run')
    timeit(c.get_all_email_apps)
    timeit(c.get_default_app)
    log.info('Second run')
    timeit(c.get_all_email_apps)
    timeit(c.get_default_app)
