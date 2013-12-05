#!/usr/bin/python
# encoding: utf-8

"""
Manage default email client and display help.

Usage:
    mailto.py <action> [<path>|<query>]

Possible actions:

config
    Show current settings

format
    Show current format

setformat
    Set new format

client [<query>]
    Show/choose email client

setclient <path>
    Set the email client to use to application at <path>.
    Called when an option in the above call is selected

help
    Display brief help (in Alfred)

openhelp
    Open the help.html file in the default application

logon
    Turn on logging (for debugging purposes)

logoff
    Turn off logging

openlog
    Open logfile in default app

dellog
    Delete the logfile.

delcache
    Delete the cache file containing the settings. Mostly for me when I fuck
    stuff up.
"""

from __future__ import print_function

import sys
import os
from subprocess import check_output, check_call
from time import time
from email.header import Header
from urllib import quote
import re

import alfred
from contacts import get_contacts, CACHEPATH
from log import logger
from settings import Settings

log = logger(u'mailto')

settings = Settings()


__usage__ = u"""
Usage:
    mailto config
    mailto format
    mailto setformat [<format>]
    mailto client [<query>]
    mailto setclient [<path>]
    mailto help
    mailto openhelp
    mailto openlog
    mailto dellog
    mailto delcache
    mailto logon
    mailto logoff
    mailto version
"""

__help__ = [
    (u"Open MailTo help file",
        u"In your browser"),
    (u"'mailtoconf' to view and change settings",
        u"View/change email client and format"),
    (u"Enter 'mailtohelp' for this message",
        u"Well, I guess you already figured this out …"),
]


#               spaces, names, MIME, no commas
DEFAULT_RULES = (True, True, True, False)


RULES = {
    u'it.bloop.airmail' : (False, False, False, False),
    u'com.eightloops.Unibox' : (True, True, False, True),
    u'com.google.Chrome' : (True, True, False, False),
    u'com.freron.MailMate' : (True, True, False, False),
}


class Formatter(object):
    """Format the mailto: URL according to client-specific rules

    See `mailto.RULES` for details.

    """

    def __init__(self, client):
        self.client = client
        self.rules = RULES.get(client, DEFAULT_RULES)
        self.use_spaces, self.use_names, self.use_mime, self.use_no_commas = self.rules
        log.debug(u'Loaded rules {!r} for client {!r}'.format(self.rules, client))

    def get_url(self, contacts, use_names=False):
        """Return formatted unicode URL for contacts

        :param contacts: list of 2-tuples: (name, email)
        :returns: string (bytes)
        """
        log.debug(u"Building URL for app '{}'".format(self.client))
        parts = []
        encoded = False
        for input in contacts:
            name, email = input
            if not self.use_names or not use_names:
                parts.append(email)
                log.debug('[not use_names] {!r} --> {!r}'.format(input, email))
                continue
            if self.use_mime:
                try:
                    name = name.encode(u'ascii')
                except UnicodeEncodeError:
                    name = str(Header(name, u'utf-8'))
                    encoded = True
            if ',' in name:
                if self.use_no_commas:
                    parts.append(email)
                    log.debug('[use_no_commas] {!r} --> {!r}'.format(input, email))
                    continue
                else:
                    name = u'"{}"'.format(name)
            log.debug('[default] {!r} --> {!r}'.format(input, name, email))
            parts.append(u'{} <{}>'.format(name, email))
        if self.use_spaces:
            result = u', '.join(parts)
        else:
            result = u','.join(parts)
        result = result.encode('utf-8')
        if encoded:  # also needs quoting
            result = quote(result)
        return 'mailto:{}'.format(result)


class MailTo(object):

    _match_bundle_id = re.compile(r'kMDItemCFBundleIdentifier = "(.+)"').match

    def __init__(self):
        self._settings = Settings()
        log.debug(u'Loaded settings : {!r}'.format(self._settings))
        self._all_apps = None
        self._contacts = None

    def get_use_contact_name(self):
        """Return bool re whether name should be used as well as address"""
        return self._settings.get(u'use_name', True)

    def set_use_contact_name(self, bool):
        """Set whether or not to use contact name as well as address"""
        self._settings[u'use_name'] = bool
        # self._save_settings()

    use_contact_name = property(get_use_contact_name, set_use_contact_name)

    def build_url(self, emails):
        """Return mailto: URL built according to Formatter"""
        if self._contacts is None:
            self._contacts = dict(get_contacts()[0])  # email:name

        formatter = Formatter(self.default_app[2])  # get by bundle id
        contacts = [(self._contacts.get(email), email) for email in emails]
        return formatter.get_url(contacts, self.use_contact_name)

    def get_default_app(self):
        """Return (appname, path) to default mail app

        Return (None, None) if no default is set.
        """
        path, bundleid = self._settings.get(u'default_app')
        if path is None:
            bundleid = self._settings.get(u'system_default_app')
            if not bundleid:
                return (None, None, None)
            else:
                return (None, None, bundleid)
        return (self._appname(path), path, bundleid)

    def set_default_app(self, path=None):
        """Set default app to use by path to application

        If path is None, the default will be deleted
        """
        if not path:
            self._settings[u'default_app'] = (None, None)
        else:
            self._settings[u'default_app'] = (path, self._bundleid(path))

    default_app = property(get_default_app, set_default_app)

    def get_logging(self):
        return self._settings['logging']

    def set_logging(self, value):
        if value:
            self._settings[u'logging'] = True
            log.debug(u'Logging ON')
        else:
            self._settings[u'logging'] = False
            log.debug(u'Logging OFF')

    logging = property(get_logging, set_logging)

    @property
    def all_apps(self):
        """Return list of apps in /Applications and ~/Applications

        Returns:
            list of tuples (appname, path)
        """
        t = time()
        if self._all_apps is None:
            command = [
                 u'mdfind',
                 u'-onlyin', u'/Applications',
                 u'-onlyin', os.path.expanduser(u'~/Applications'),
                 u'kMDItemContentTypeTree:com.apple.application-bundle'
            ]
            lines = check_output(command).decode(u'utf-8').split(u'\n')
            app_paths = [s.strip() for s in lines if s.strip()]
            self._all_apps = [(self._appname(p), p) for p in app_paths]
        log.debug(u'All apps listed in {:0.4f} secs'.format(time() - t))
        return self._all_apps

    def _appname(self, path):
        """Get app name from path"""
        return os.path.splitext(os.path.basename(path))[0]

    def _bundleid(self, app_path):
        """Return the bundle ID for Application at app_path"""
        command = [u'mdls', u'-name', u'kMDItemCFBundleIdentifier', app_path]
        m = self._match_bundle_id(check_output(command).strip())
        if not m:
            raise ValueError("Could not find bundle ID for '{}'".format(app_path))
        return m.groups()[0]


def show_help():
    items = []
    for text, subtext in __help__:
        item = alfred.Item(
            {u'valid':u'yes'},
            text,
            subtext,
            icon=u'info.png'
        )
        items.append(item)
    print(alfred.xml(items, maxresults=25))


def open_help_file():
    """Open help.html with default app"""
    command = [u'open', os.path.join(os.path.dirname(__file__), u'help.html')]
    log.debug(u'help command : {}'.format(command))
    retcode = check_call(command)
    if retcode != 0:
        sys.exit(retcode)


def show_config():
    """Show current settings"""
    log.debug(u'show_config')
    mt = MailTo()
    use_name = mt.use_contact_name
    appname, path, bundleid = mt.default_app
    # email client
    items = []
    if not appname:
        appname = u'System Default'
        path = u''
    items.append( alfred.Item(
        {u'valid':u'no'},
         u'Current Email Client: {}'.format(appname),
         path,
         icon=u'icon.png')
    )
    items.append(alfred.Item({u'valid':u'yes', u'arg':u'client'},
                              u'Change Client …',
                              u'', icon=u'icon.png'))
    if use_name:
        title = u'Current Format: Default (Name & Email)'
        subtitle = u'Email-only will be used with some problem clients'
    else:
        title = u'Current Format: Email Only'
        subtitle = u'E.g. bob.smith@example.com, joan@example.com'
    items.append( alfred.Item(
        {u'valid':u'no'},
         title,
         subtitle,
         icon=u'icon.png')
    )
    items.append(alfred.Item({u'valid':u'yes', u'arg':u'format'},
                              u'Change Format …',
                              u'', icon=u'icon.png'))
    print(alfred.xml(items))


def choose_format():
    """Choose email format"""
    items = []
    mt = MailTo()
    use_name = mt.use_contact_name
    if use_name:
        title = u'Current Setting: Default (Name & Email)'
        subtitle = u'Email-only will be used with some problem clients'
    else:
        title = u'Current Setting: Email Only'
        subtitle = u'E.g. bob.smith@example.com, joan@example.com'
    items.append( alfred.Item(
        {u'valid':u'no'},
         title,
         subtitle,
         icon=u'icon.png')
    )
    options = {
        u'email' : alfred.Item({u'valid':u'yes', u'arg':u'email'},
                               u'Call Email Client with Email Only',
                               u'e.g. bob.smith@example.com',
                               icon=u'icon.png'),
        u'default' : alfred.Item({u'valid':u'yes', u'arg':u'name'},
                               u'Use Default Format (Name & Email)',
                               u'Name and email except with known problem clients',
                               icon=u'icon.png')
    }
    if use_name:
        items.append(options[u'email'])
    else:
        items.append(options[u'default'])
    print(alfred.xml(items))


def choose_client(query):
    """Choose a new email client"""
    log.debug(u'choose_client : {!r}'.format(query))
    query = query.lower()
    mt = MailTo()
    current_app, current_path, current_bundleid = mt.default_app
    apps = mt.all_apps
    hits = []
    items = []
    if query == u'':  # Show current setting
        if not current_app:
            appname = u'System Default'
            path = u''
        else:
            appname = current_app
            path = current_path
        items.append( alfred.Item(
            {u'valid':u'no'},
             u'Current Email Client: {}'.format(appname),
             path,
             icon=u'icon.png')
        )
    # Show other options
    if current_app is not None and query == u'':
        items.append(alfred.Item(
            {u'valid':u'yes',
             u'arg':u'',
             u'autocomplete':u'System Default',
            },
            u'System Default Email Client',
            u'Use system default email client with MailTo',
            icon=u'icon.png')
        )
    for appname, path in apps:
        if appname.lower().startswith(query):
            hits.append((appname, path))
            # log.debug(u'Hit : {}'.format(appname))
    for appname, path in apps:
        if query in appname.lower() and (appname, path) not in hits:
            hits.append((appname, path))
            # log.debug(u'Hit : {}'.format(appname))
    log.debug(u"{} matches for '{}'".format(len(hits), query))
    if not hits and not items:
        return
    for appname, path in hits:
        if path == current_path:
            items.append(alfred.Item(
                {u'valid':u'no'
                 # u'uid':path
                },
                u'{} (current client)'.format(appname),
                path,
                icon=(path, {u'type':u'fileicon'}))
            )
        else:
            items.append(alfred.Item(
                {u'valid':u'yes',
                 u'arg':path,
                 u'autocomplete':appname,
                 # u'uid':path
                },
                appname,
                path,
                icon=(path, {u'type':u'fileicon'}))
            )
    print(alfred.xml(items))


def main():
    from docopt import docopt
    args = alfred.args()
    log.debug(u'alfred.args : {}'.format(args))
    args = docopt(__usage__, args)
    log.debug(u'docopt.args : {}'.format(args))

    # application actions
    if args.get(u'config'):  # show configuration
        show_config()

    # email client
    elif args.get(u'client'):  # choose client
        query = args.get(u'<query>')
        if not query:
            query = u''
        query = query.strip()
        choose_client(query)
    elif args.get(u'setclient'):  # set default mail client
        path = args.get(u'<path>')
        log.debug(u'setclient : {!r}'.format(path))
        mt = MailTo()
        if not path:
            mt.default_app = None
            print(u'System Default')
        else:
            mt.default_app = path
            appname = mt.default_app[0]
            print(appname)

    # email format
    elif args.get(u'format'):  # set email format
        choose_format()
    elif args.get(u'setformat'):  # set default format
        fmt = args.get(u'<format>')
        log.debug(u'setformat : {!r}'.format(fmt))
        mt = MailTo()
        # if not fmt:
        #     mt.use_contact_name = True
        #     print(u'Default Format (Name & Email Address)')
        if fmt == u'name':
            mt.use_contact_name = True
            print(u'Default Format (Name & Email Address)')
        elif fmt == u'email':
            mt.use_contact_name = False
            print(u'Email Address Only')

    # other options
    elif args.get(u'delcache'):  # delete settings file
        deleted = False
        if os.path.exists(settings.settings_path):
            os.unlink(settings.settings_path)
            print('Deleted settings', file=sys.stderr)
            deleted = True
        if os.path.exists(CACHEPATH):
            os.unlink(CACHEPATH)
            print('Deleted cache', file=sys.stderr)
            deleted = True
        if not deleted:
            print('No cache to delete', file=sys.stderr)
    elif args.get(u'dellog'):  # delete logfile
        if os.path.exists(settings.log_path):
            os.unlink(settings.log_path)
            print('Deleted log file', file=sys.stderr)
    elif args.get(u'logon'):  # turn on logging
        mt = MailTo()
        mt.logging = True
        print('Turned logging on', file=sys.stderr)
    elif args.get(u'logoff'):  # turn off logging
        mt = MailTo()
        mt.logging = False
        print('Turned logging off', file=sys.stderr)
    elif args.get(u'openlog'):  # open logfile
        check_call([u'open', settings.log_path])
    elif args.get(u'help'):  # show help in Alfred
        show_help()
    elif args.get(u'openhelp'):  # open help file in browser
        open_help_file()
    elif args.get(u'version'):  # print version
        print(open(os.path.join(os.path.dirname(__file__), 'version')).read().strip())
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        log.exception(err)
