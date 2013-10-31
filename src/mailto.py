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


# import logging
# logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), u'debug.log'),
#                     level=logging.DEBUG)
# log = logging.getLogger(u'mailto')


__usage__ = u"""
Usage:
    mailto select [<query>]
    mailto set <path>
    mailto get
    mailto help
    mailto openhelp
    mailto clear
    mailto delcache
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


class MailApps(object):

    def __init__(self):
        self._settings = self._load_settings()
        self._all_apps = None

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
        # log.debug(u'All apps listed in {:0.4f} secs'.format(time() - t))
        return self._all_apps

    def _load_settings(self):
        if not os.path.exists(SETTINGS_CACHE):
            return dict(default_app=None, clients=[])
        with open(SETTINGS_CACHE) as file:
            return json.load(file)

    def _save_settings(self):
        with open(SETTINGS_CACHE, u'wb') as file:
            json.dump(self._settings, file, indent=2)

    def _appname(self, path):
        """Get app name from path"""
        return os.path.splitext(os.path.basename(path))[0]


def select_app(query):
    """Show list of apps matching `query`"""
    query = query.lower()
    hits = []
    apps = MailApps().all_apps
    for appname, path in apps:
        if appname.lower().startswith(query):
            hits.append((appname, path))
            # log.debug(u'Hit : {}'.format(appname))
    for appname, path in apps:
        if query in appname.lower() and (appname, path) not in hits:
            hits.append((appname, path))
            # log.debug(u'Hit : {}'.format(appname))
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
    # log.debug(u'help command : {}'.format(command))
    retcode = check_call(command)
    if retcode != 0:
        sys.exit(retcode)


def clear_default():
    MailApps().default_app = None
    item = alfred.Item(
        {u'valid':u'no',
         u'uid':u'0'},
         u'Default email client has been reset to system default',
         u'',
         icon=u'icon.png'
    )
    print(alfred.xml([item]))


def show_default():
    """Output default app"""
    appname, path = MailApps().default_app
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


def main():
    from docopt import docopt
    args = docopt(__usage__, alfred.args())
    # log.debug(u'args : {}'.format(args))
    if args.get(u'get'):
        show_default()
    elif args.get(u'set'):
        path = args.get(u'<path>')
        # log.debug(u'Setting default client to : {}'.format(path))
        ma = MailApps()
        ma.default_app = path
        print(ma.default_app[0])
    elif args.get(u'select'):
        query = args.get(u'<query>')
        # log.debug(u'Select app based on : {}'.format(query))
        select_app(query)
    elif args.get(u'help'):
        show_help()
    elif args.get(u'clear'):
        clear_default()
    elif args.get(u'delcache'):
        if os.path.exists(SETTINGS_CACHE):
            os.unlink(SETTINGS_CACHE)
    elif args.get(u'openhelp'):
        open_help_file()
    return 0

if __name__ == '__main__':
    sys.exit(main())