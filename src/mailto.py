#!/usr/bin/env python
# encoding: utf-8

"""
Manage default email client and display help.

Usage:
    mailto.py <action> [<path>|<query>]

Possible actions:

client [<query>]
    Show/choose email client

set <path>
    Set the email client to use to application at <path>.
    Called when an option in the above call is selected

help
    Display brief help (in Alfred)

openhelp
    Open the help.html file in the default application

usename
    Set format of recipients sent to email client

delcache
    Delete the cache file containing the settings. Mostly for me when I fuck
    stuff up.
dellog
    Delete the logfile.
"""

from __future__ import print_function

import sys
import os
import json
from subprocess import check_output, check_call
from time import time

import alfred
from contacts import get_contacts
from log import logger

log = logger(u'mailto')


__usage__ = u"""
Usage:
    mailto help
    mailto openhelp
    mailto client [<query>]
    mailto usename [yes|no|clear]
    mailto set <path>
    mailto delcache
    mailto dellog
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

def do_client(value=None):
    """Get/set email client"""
    log.debug(u'do_client : {!r}'.format(value))
    mt = MailTo()

    # show settings
    items = []
    appname, path = mt.default_app
    if not appname:
        appname = u'System Default'
        path = u''
    items.append( alfred.Item(
        {u'valid':u'no',
         u'uid':u'0'},
         u'Current Email Client: {}'.format(appname),
         path,
         icon=u'icon.png')
    )
    if mt.default_app[0] is not None:
        items.append(alfred.Item({u'valid':u'yes', u'arg':u'',
                                  u'uid':0},
                                  u'Use System Default Email Client',
                                  u'', icon=u'icon.png'))
    items.append(alfred.Item({u'valid':u'no', u'uid':1},
                              u'Type an App Name to Select a New Client…',
                              u'', icon=u'icon.png'))
    print(alfred.xml(items))


def choose_client(query):
    """Choose a new email client"""
    log.debug(u'choose_client : {!r}'.format(query))
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
             u'uid':path
            },
            u'Use {} with MailTo'.format(appname),
            u'',
            icon=(path, {u'type':u'fileicon'})
        )
        items.append(item)
    print(alfred.xml(items))


def do_usename(value=None):
    """Get/set format of output sent to email client"""
    log.debug(u'do_usename : {!r}'.format(value))
    mt = MailTo()
    if value is True:
        mt.use_contact_name = True
        print(u'Name and email address')
    elif value is False:
        mt.use_contact_name = False
        print(u'Email address only')
    else:  # show some options
        items = []
        use_name = mt.use_contact_name
        title = u'Current Setting: Default (Name & Email)'
        subtitle = u'Email-only will be used with some problem clients'
        if use_name is True:
            title = u'Current Setting: Name & Email'
            subtitle = u'E.g. Bob Smith <bob@example.com>, Joan Jones <joan@example.com>'
        elif use_name is False:
            title = u'Current Setting: Email Only'
            subtitle = u'E.g. bob.smith@example.com, joan@example.com'
        items.append( alfred.Item(
            {u'valid':u'no',
             u'uid':u'0'},
             title,
             subtitle,
             icon=u'icon.png')
        )
        options = {
            u'email' : alfred.Item({u'valid':u'yes', u'arg':u'no'},
                                   u'Call Email Client with Email Only',
                                   u'e.g. bob.smith@example.com',
                                   icon=u'icon.png'),
            u'name' : alfred.Item({u'valid':u'yes', u'arg':u'yes'},
                                   u'Call Email Client with Name and Email',
                                   u'e.g. Bob Smith <bob.smith@example.com>',
                                   icon=u'icon.png'),
            u'default' : alfred.Item({u'valid':u'yes', u'arg':u'clear'},
                                   u'Use Default Format',
                                   u'Name and email except with known problem clients',
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
    args = alfred.args()
    log.debug(u'alfred.args : {}'.format(args))
    args = docopt(__usage__, args)
    log.debug(u'docopt.args : {}'.format(args))
    if args.get(u'set'):  # set new default email client
        path = args.get(u'<path>').strip()
        if path == u'':
            path = None
        log.debug(u'Setting default client to : {}'.format(path))
        mt = MailTo()
        mt.default_app = path
        appname = mt.default_app[0]
        if appname is None:
            appname = u'System Default'
        print(appname)
    if args.get(u'help'):  # show help in Alfred
        show_help()
    elif args.get(u'delcache'):  # delete settings file
        if os.path.exists(SETTINGS_CACHE):
            os.unlink(SETTINGS_CACHE)
    elif args.get(u'dellog'):  # delete logfile
        if os.path.exists(LOGFILE):
            os.unlink(LOGFILE)
    elif args.get(u'openhelp'):  # open help file in browser
        open_help_file()
    elif args.get(u'client'):  # show client settings
        if args.get(u'<query>'):
            query = args.get(u'<query>')
            if query == u'':
                do_client()
            else:
                choose_client(query)
        else:
            do_client()
    elif args.get(u'usename'):  # set recipient formatting
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