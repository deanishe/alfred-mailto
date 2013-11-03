#!/usr/bin/env python
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
import json
from subprocess import check_output, check_call
from time import time

import alfred
from contacts import get_contacts
from log import logger, LOGFILE

log = logger(u'mailto')


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
"""

__help__ = [
    (u"Open MailTo help file",
        u"In your browser"),
    (u"'mailtoconf' to view and change settings",
        u"View/change email client and format"),
    (u"Enter 'mailtohelp' for this message",
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


def show_config():
    """Show current settings"""
    log.debug(u'show_config')
    mt = MailTo()
    use_name = mt.use_contact_name
    appname, path = mt.default_app
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
    # address format
    title = u'Current Format: Default (Name & Email)'
    subtitle = u'Email-only will be used with some problem clients'
    if use_name is True:
        title = u'Current Format: Name & Email'
        subtitle = u'E.g. Bob Smith <bob@example.com>, Joan Jones <joan@example.com>'
    elif use_name is False:
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
    title = u'Current Setting: Default (Name & Email)'
    subtitle = u'Email-only will be used with some problem clients'
    if use_name is True:
        title = u'Current Setting: Name & Email'
        subtitle = u'E.g. Bob Smith <bob@example.com>, Joan Jones <joan@example.com>'
    elif use_name is False:
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
        u'name' : alfred.Item({u'valid':u'yes', u'arg':u'name'},
                               u'Call Email Client with Name and Email',
                               u'e.g. Bob Smith <bob.smith@example.com>',
                               icon=u'icon.png'),
        u'default' : alfred.Item({u'valid':u'yes', u'arg':u''},
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


def choose_client(query):
    """Choose a new email client"""
    log.debug(u'choose_client : {!r}'.format(query))
    query = query.lower()
    mt = MailTo()
    current_app = mt.default_app[0]
    apps = mt.all_apps
    hits = []
    items = []
    if current_app is not None:
        items.append(alfred.Item(
            {u'valid':u'yes',
             u'arg':u'',
             u'autocomplete':u'System Default',
            },
            u'Use System Default Email Client',
            u'',
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
        items.append(alfred.Item(
            {u'valid':u'yes',
             u'arg':path,
             u'autocomplete':appname,
             u'uid':path
            },
            u'Use {}'.format(appname),
            u'',
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
        if not fmt:
            mt.use_contact_name = None
            print(u'Default Format')
        elif fmt == u'name':
            mt.use_contact_name = True
            print(u'Name and Email Address')
        elif fmt == u'email':
            mt.use_contact_name = False
            print(u'Email Address Only')

    # other options
    elif args.get(u'delcache'):  # delete settings file
        if os.path.exists(SETTINGS_CACHE):
            os.unlink(SETTINGS_CACHE)
    elif args.get(u'dellog'):  # delete logfile
        if os.path.exists(LOGFILE):
            os.unlink(LOGFILE)
    elif args.get(u'openlog'):  # open logfile
        check_call([u'open', LOGFILE])
    elif args.get(u'help'):  # show help in Alfred
        show_help()
    elif args.get(u'openhelp'):  # open help file in browser
        open_help_file()
    return 0


if __name__ == '__main__':
    sys.exit(main())
