#!/usr/bin/env python
# encoding: utf-8

"""
Manage default email client and display help.

Usage:
    mailto.py <action> [<path> | <query>]

Possible actions:

select <query>
    Display a list of candidate apps matching query

set <path>
    Set the email client to use to application at <path>.
    Called when an option in the above call is selected

get
    Display (in Alfred) the currently-selected email client

help
    Display brief help (in Alfred)

openhelp
    Open the help.html file in the default application

clear
    Delete the selected email client (i.e. revert to system default email client)

delcache
    Delete the cache file containing the settings. Mostly for me when I fuck 
    stuff up.
"""

from __future__ import print_function

import sys
import os
import json
from subprocess import check_output, check_call
from time import time

import alfred
from contacts import get_contacts

import logging
logging.basicConfig(filename=os.path.join(alfred.work(True), u'debug.log'),
                    level=logging.DEBUG)
log = logging.getLogger(u'search')


__usage__ = u"""
Usage:
    mailto select [<query>]
    mailto set <path>
    mailto get
    mailto help
    mailto openhelp
    mailto clear
    mailto delcache
    mailto usename [yes|no|clear]
"""

__help__ = [
    (u"Open MailTo help file",
        u"In your browser"),
    (u"'mailto setdefault' to choose email client",
        u"Only if you don't want to use your system default email client"),
    (u"'mailto getdefault' to see current client",
     u"In case youve forgotten"),
    (u"'mailto cleardefault' to delete current client",
        u"And go back to using the system default email client"),
    (u"Enter 'mailto help' for this message",
        u"Well, I guess you already figured this out …"),
]


SETTINGS_CACHE = os.path.join(alfred.work(False), u'mailto.json')

# Don't like names in mailto: URLs
KNOWN_BAD_CLIENTS = [u'Airmail']

CLEAR = object()


class MailTo(object):

    def __init__(self):
        self._settings = self._load_settings()
        log.debug(u'Loaded settings : {!r}'.format(self._settings))
        self._all_apps = None
        self._contacts = None

    def get_use_contact_name(self):
        """Return bool re whether name should be used as well as address"""
        return self._settings.get(u'use_name', None)

    def set_use_contact_name(self, bool):
        """Set whether or not to use contact name as well as address"""
        self._settings[u'use_name'] = bool
        self._save_settings()

    use_contact_name = property(get_use_contact_name, set_use_contact_name)

    def format_recipient(self, email):
        """Return recipient formatted according to settings

        Returns:
            Bob Smith <bob.smith@example.com>
             - or -
            bob.smith@example.com
        """
        def _with_name(email):
            if self._contacts is None:
                self._contacts = dict(get_contacts()[0])  # email:name
            name = self._contacts.get(email)
            if name and name != email:
                return u'{} <{}>'.format(name, email)
            return email
        if self.use_contact_name is False:
            return email
        elif self.use_contact_name is True:
            return _with_name(email)
        else:
            if self.default_app[0] in KNOWN_BAD_CLIENTS:
                return email
            return _with_name(email)


    def get_default_app(self):
        """Return (appname, path) to default mail app

        Return (None, None) if no default is set.
        """
        path = self._settings.get(u'default_app')
        if path is None:
            return (None, None)
        return (self._appname(path), path)

    def set_default_app(self, path=None):
        """Set default app to use by path to application

        If path is None, the default will be deleted
        """
        self._settings[u'default_app'] = path
        self._save_settings()

    default_app = property(get_default_app, set_default_app)

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
                 u'kind:application'
            ]
            lines = check_output(command).decode(u'utf-8').split(u'\n')
            app_paths = [s.strip() for s in lines if s.strip()]
            self._all_apps = [(self._appname(p), p) for p in app_paths]
        log.debug(u'All apps listed in {:0.4f} secs'.format(time() - t))
        return self._all_apps

    def _load_settings(self):
        if not os.path.exists(SETTINGS_CACHE):
            return dict(default_app=None, clients=[], use_name=None)
        with open(SETTINGS_CACHE) as file:
            return json.load(file)

    def _save_settings(self):
        log.debug(u'Saving settings : {}'.format(self._settings))
        with open(SETTINGS_CACHE, u'wb') as file:
            json.dump(self._settings, file, indent=2)

    def _appname(self, path):
        """Get app name from path"""
        return os.path.splitext(os.path.basename(path))[0]


def select_app(query):
    """Show list of apps matching `query`"""
    query = query.lower()
    hits = []
    apps = MailTo().all_apps
    for appname, path in apps:
        if appname.lower().startswith(query):
            hits.append((appname, path))
            log.debug(u'Hit : {}'.format(appname))
    for appname, path in apps:
        if query in appname.lower() and (appname, path) not in hits:
            hits.append((appname, path))
            log.debug(u'Hit : {}'.format(appname))
    if not hits:
        return
    items = []
    for appname, path in hits:
        item = alfred.Item(
            {u'valid':u'yes',
             u'arg':path,
             u'autocomplete':appname,
             u'uid':appname
            },
            u'Use {} for MailTo'.format(appname),
            u'',
            icon=(path, {u'type':u'fileicon'})
        )
        items.append(item)
    print(alfred.xml(items))


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


def clear_default():
    MailTo().default_app = None
    print(u'Default system email client will be used')


def show_default():
    """Output default app"""
    appname, path = MailTo().default_app
    if appname is None:
        appname = u'System Default'
    item = alfred.Item(
        {u'valid':u'no',
         u'uid':u'0'},
         u'Default MailTo client : {}'.format(appname),
         u'',
         icon=(path, {u'type':u'fileicon'})
    )
    print(alfred.xml([item]))


def do_usename(value=None):
    """Get/set format of output sent to email client"""
    log.debug(u'do_usename : {!r}'.format(value))
    ma = MailTo()
    if value is True:
        ma.use_contact_name = True
        print(u'Name and email address')
    elif value is False:
        ma.use_contact_name = False
        print(u'Email address only')
    elif value is CLEAR:
        ma.use_contact_name = None
        print(u'Reset to default')
    else:  # show some options
        items = []
        use_name = ma.use_contact_name
        title = u'Current setting'
        subtitle = u'Default: Name and email except with known bad clients'
        if use_name is True:
            subtitle = u'Name and email: Bob Smith <bob.smith@example.com>'
        elif use_name is False:
            subtitle = u'Email only: bob.smith@example.com'
        items.append( alfred.Item(
            {u'valid':u'no',
             u'uid':u'0'},
             title,
             subtitle,
             icon=u'icon.png')
        )
        options = {
            u'email' : alfred.Item({u'valid':u'yes', u'arg':u'no'},
                                   u'Call mail client with email only',
                                   u'e.g. bob.smith@example.com',
                                   icon=u'icon.png'),
            u'name' : alfred.Item({u'valid':u'yes', u'arg':u'yes'},
                                   u'Call mail client with name and email',
                                   u'e.g. Bob Smith <bob.smith@example.com>',
                                   icon=u'icon.png'),
            u'default' : alfred.Item({u'valid':u'yes', u'arg':u'clear'},
                                   u'Use default format',
                                   u'Name and email except with known bad clients',
                                   icon=u'icon.png')
        }
        if use_name is True:
            items.append(options[u'email'])
            items.append(options[u'default'])
        elif use_name is False:
            items.append(options[u'name'])
            items.append(options[u'default'])
        else:
            items.append(options[u'name'])
            items.append(options[u'email'])
        print(alfred.xml(items))


def main():
    from docopt import docopt
    args = docopt(__usage__, alfred.args())
    log.debug(u'args : {}'.format(args))
    if args.get(u'get'):
        show_default()
    elif args.get(u'set'):
        path = args.get(u'<path>')
        log.debug(u'Setting default client to : {}'.format(path))
        ma = MailTo()
        ma.default_app = path
        print(ma.default_app[0])
    elif args.get(u'select'):
        query = args.get(u'<query>')
        log.debug(u'Select app based on : {}'.format(query))
        select_app(query)
    elif args.get(u'help'):
        show_help()
    elif args.get(u'delcache'):
        if os.path.exists(SETTINGS_CACHE):
            os.unlink(SETTINGS_CACHE)
    elif args.get(u'openhelp'):
        open_help_file()
    elif args.get(u'usename'):
        if args.get(u'yes'):
            do_usename(True)
        elif args.get(u'no'):
            do_usename(False)
        elif args.get(u'clear'):
            do_usename(CLEAR)
        else:
            do_usename()
    elif args.get(u'clear'):
        clear_default()
    return 0

if __name__ == '__main__':
    sys.exit(main())