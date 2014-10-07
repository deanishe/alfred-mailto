#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-10-03
#

"""mailto.py

Usage:
    mailto.py search <query>
    mailto.py config [<query>]
    mailto.py setclient <app_path>
    mailto.py toggle (format|update|help)
    mailto.py compose [<recipients>]
    mailto.py reload
    mailto.py update
    mailto.py help
"""

from __future__ import print_function, unicode_literals, absolute_import

from argparse import ArgumentParser
import os
from pipes import quote
import re
import subprocess
import sys

from workflow import Workflow

from common import run_alfred

log = None

email_valid = re.compile(r'[^@]+@[^@]+\.[^@]+').match

# Update settings
with open(os.path.join(os.path.dirname(__file__), 'version')) as file_obj:
    __version__ = file_obj.read().strip()

UPDATE_INTERVAL = 1  # day
GITHUB_REPO = 'deanishe/alfred-mailto'

# Called to re-open settings
CONFIG_KEYWORD = 'mailto'

# Query segment separator
SEPARATOR = '⟩'

# Workflow icons
ICON_CONFIG = 'icons/config-purple.icns'
# ICON_CONFIG_FORMAT = 'icons/config-blue.icns'
# ICON_CONFIG_NOTIFY = 'icons/config-purple.icns'
ICON_COMPANY = 'icons/company.icns'
ICON_COMPOSE = 'icons/compose.icns'
ICON_GROUP = 'icons/group.icns'
ICON_HELP = 'icons/help.icns'
ICON_PERSON = 'icons/person.icns'
ICON_RELOAD = 'icons/reload.icns'
ICON_VERSION_NEW = 'icons/update-available.icns'
ICON_VERSION_OK = 'icons/update-none.icns'
ICON_WARNING = 'icons/warning.icns'


DEFAULT_SETTINGS = {
    'use_name': True,  # Use contact names and emails by default
    'notify_updates': True,  # Show user when a new version is available
    'show_help': True,  # Show help text in subtitles
}


# ooo        ooooo            o8o  oooo  ooooooooooooo
# `88.       .888'            `"'  `888  8'   888   `8
#  888b     d'888   .oooo.   oooo   888       888       .ooooo.
#  8 Y88. .P  888  `P  )88b  `888   888       888      d88' `88b
#  8  `888'   888   .oP"888   888   888       888      888   888
#  8    Y     888  d8(  888   888   888       888      888   888
# o8o        o888o `Y888""8o o888o o888o     o888o     `Y8bod8P'

class MailToApp(object):

    def __init__(self):
        self.wf = wf
        self.validator = None

    def run(self, wf):
        self.wf = wf
        self.args = self._parse_args()
        log.debug('args : {}'.format(self.args))
        method_name = 'do_{}'.format(self.args.action)
        if not hasattr(self, method_name):
            raise ValueError('Invalid action : {}'.format(self.args.action))
        return getattr(self, method_name)()

    #                                              dP
    #                                              88
    # .d8888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d888b.
    # Y8ooooo. 88ooood8 88'  `88 88'  `88 88'  `"" 88'  `88
    #       88 88.  ... 88.  .88 88       88.  ... 88    88
    # `88888P' `88888P' `88888P8 dP       `88888P' dP    dP

    def do_search(self):
        """Search contacts"""
        from contacts import Contacts

        log.debug('Searching contacts')

        query = self.args.query

        # Notify of update
        if self.wf.settings.get('notify_updates', True):
            if self.wf.update_available:
                version = wf.cached_data('__workflow_update_status',
                                         max_age=0)['version']

                self.wf.add_item(
                    'Version {} is available'.format(version),
                    ('↩ to install new version, '
                     '"{}" to turn off notifications'.format(CONFIG_KEYWORD)),
                    valid=True,
                    arg='update',
                    icon=ICON_VERSION_NEW,)

        # Load cached contacts
        contacts = Contacts()

        if contacts.updating:
            self.wf.add_item('Updating contacts …', icon=ICON_RELOAD)

        if contacts.empty:
            self.wf.add_item('Contacts not yet cached',
                             'Please wait a second or two',
                             icon=ICON_WARNING)

            self.wf.send_feedback()
            return 0

        if not query:
            subtitle = ('↩ to compose a new email or start typing to '
                        'add recipients')

            if not self.wf.settings.get('show_help', True):
                subtitle = None

            self.wf.add_item('Compose a new email',
                             subtitle,
                             valid=True,
                             arg='compose',
                             icon=ICON_COMPOSE)

            self.wf.send_feedback()
            return 0

        # Extract email addresses from query
        query = query.lower()
        emails = []
        invalid_emails = []
        existing = []

        if ',' in query:
            emails = [s.strip() for s in query.split(',')]

            if len(emails):
                existing = []
                for email in emails[:-1]:

                    if not email_valid(email):
                        invalid_emails.append(email)

                    else:
                        existing.append(email)

                query = emails[-1]

        log.debug(
            'existing : {!r} emails : {!r} invalid_emails : {!r} query : {!r}'
            .format(existing, emails, invalid_emails, query))

        # Show errors first
        if invalid_emails:
            for email in invalid_emails:
                self.wf.add_item('{} is not a valid email address'.format(
                                 email),
                                 icon=ICON_WARNING)

        ################################################################
        # Main results
        ################################################################

        hits = []
        recipients = []

        if query:
            hits = contacts.search(query)

        log.debug('{} matches for `{}`'.format(len(hits), query))

        # No matches, offer to compose message if there are valid recipients
        if not hits:

            if existing:

                recipients = existing[:]

            if query:
                if not email_valid(query):
                    self.wf.add_item(
                        '{} is not a valid email address'.format(
                            query),
                        icon=ICON_WARNING)

                else:   # Offer to mail query and/or existing recipients
                    recipients.append(query)

            recipients = ', '.join(recipients)
            log.debug('recipients : {}'.format(recipients))

            subtitle = ''

            if self.wf.settings.get('show_help', True):
                subtitle = 'Hit ↩ to compose a new message'

            self.wf.add_item('Compose mail to {}'.format(recipients),
                             subtitle,
                             autocomplete=recipients + ', ',
                             valid=True,
                             arg='compose ' + quote(recipients),
                             icon=ICON_COMPOSE)

        # Show results
        for item in hits:

            if item['email'] in existing:
                log.debug('Ignoring duplicate : {}'.format(item))
                continue

            icon = ICON_PERSON

            if item['is_group']:
                icon = ICON_GROUP

            elif item['is_company']:
                icon = ICON_COMPANY

            recipients = ', '.join(existing[:] + [item['email']])

            subtitle = item['email']

            if self.wf.settings.get('show_help', True):
                subtitle += '  //  ⇥ to add, ↩ to add+compose'

            self.wf.add_item(item['name'],
                             subtitle,
                             uid=item['email'],
                             autocomplete=recipients + ', ',
                             valid=True,
                             arg='compose ' + quote(recipients),
                             icon=icon)

        self.wf.send_feedback()
        return

    # .d8888b. .d8888b. 88d8b.d8b. 88d888b. .d8888b. .d8888b. .d8888b.
    # 88'  `"" 88'  `88 88'`88'`88 88'  `88 88'  `88 Y8ooooo. 88ooood8
    # 88.  ... 88.  .88 88  88  88 88.  .88 88.  .88       88 88.  ...
    # `88888P' `88888P' dP  dP  dP 88Y888P' `88888P' `88888P' `88888P'
    #                              88
    #                              dP

    def do_compose(self):
        """Build mailto: URL and open with configured app"""
        log.debug('Composing email ...')
        from client import Client
        from common import command_output

        query = self.args.query
        log.debug('Composing email to {}'.format(query))
        client = Client()
        emails = [s.strip() for s in query.split(',') if s.strip()]
        url = client.build_url(emails)
        log.debug('URL : {!r}'.format(url))

        cmd = ['open']

        app = client.default_app

        log.debug('default_app : {}'.format(app))

        if app:
            cmd += ['-b', app['bundleid']]

        cmd.append(url)
        command_output(cmd)

    #                   dP                         dP
    #                   88                         88
    # 88d888b. .d8888b. 88 .d8888b. .d8888b. .d888b88
    # 88'  `88 88ooood8 88 88'  `88 88'  `88 88'  `88
    # 88       88.  ... 88 88.  .88 88.  .88 88.  .88
    # dP       `88888P' dP `88888P' `88888P8 `88888P8

    def do_reload(self):
        """Force update of contacts cache"""
        from contacts import Contacts
        log.debug('Forcing cache update ...')
        Contacts().update(force=True)
        self.notify('Refreshing contacts and app caches…')
        return 0

    #                         dP            dP
    #                         88            88
    # dP    dP 88d888b. .d888b88 .d8888b. d8888P .d8888b.
    # 88    88 88'  `88 88'  `88 88'  `88   88   88ooood8
    # 88.  .88 88.  .88 88.  .88 88.  .88   88   88.  ...
    # `88888P' 88Y888P' `88888P8 `88888P8   dP   `88888P'
    #          88
    #          dP

    def do_update(self):
        """Check for new version of the workflow"""

        available = self.wf.start_update()

        if available:
            self.notify('Installing new version…')

        else:
            self.notify('No new version available')

    # dP                dP
    # 88                88
    # 88d888b. .d8888b. 88 88d888b.
    # 88'  `88 88ooood8 88 88'  `88
    # 88    88 88.  ... 88 88.  .88
    # dP    dP `88888P' dP 88Y888P'
    #                      88
    #                      dP

    def do_help(self):
        """Open help file in browser"""
        log.debug('Opening README in browser ...')
        cmd = ['open', wf.workflowfile('README.html')]
        subprocess.call(cmd)

    #                            .8888b oo
    #                            88   "
    # .d8888b. .d8888b. 88d888b. 88aaa  dP .d8888b.
    # 88'  `"" 88'  `88 88'  `88 88     88 88'  `88
    # 88.  ... 88.  .88 88    88 88     88 88.  .88
    # `88888P' `88888P' dP    dP dP     dP `8888P88
    #                                           .88
    #                                       d8888P

    def do_config(self):
        """Show configuration"""
        from client import Client
        client = Client()
        log.debug('Showing settings')

        query = self.args.query
        log.debug('query : {}'.format(query))

        # Go back
        if query.endswith(SEPARATOR):  # User deleted trailing space
            run_alfred('{} '.format(CONFIG_KEYWORD))

        # Parse subqueries and dispatch to appropriate method
        if SEPARATOR in query:
            parts = [s.strip() for s in query.split(SEPARATOR) if s.strip()]
            log.debug('parts : {}'.format(parts))

            if parts:
                action = parts[0]
                if len(parts) > 1:
                    query = parts[1]
                else:
                    query = None

                if action == 'Client':
                    return self.choose_client(query)
                else:
                    self.wf.add_item('Unknown setting : {}'.format(action),
                                     'Try a different query',
                                     icon=ICON_WARNING)

                    self.wf.send_feedback()
                    return

        items = []
        help_text = '  //  ↩ to change'

        # Update status
        if self.wf.update_available:

            version = wf.cached_data(
                '__workflow_update_status', max_age=0)['version']

            items.append(
                dict(
                    title='Version {} is available'.format(version),
                    subtitle='↩ to update',
                    valid=True,
                    arg='update',
                    icon=ICON_VERSION_NEW,
                )
            )

        else:  # Current version

            items.append(
                dict(
                    title='MailTo is up to date (v{})'.format(__version__),
                    subtitle='↩ to check for update now',
                    valid=True,
                    arg='update',
                    icon=ICON_VERSION_OK,
                )
            )

        # Reload
        items.append(
            dict(
                title='Force Reload',
                subtitle='↩ to reload contacts and applications now',
                valid=True,
                arg='reload',
                icon=ICON_RELOAD
            )
        )

        # Client
        app = self.wf.settings.get('default_app')

        if app:
            appname = app['name']
            path = app['path']

        else:
            appname = 'System Default'
            path = client.system_default_app['path']

        items.append(
            dict(
                title='Email Client: {}'.format(appname),
                subtitle='↩ to change',
                valid=False,
                autocomplete=' {} Client {} '.format(SEPARATOR, SEPARATOR),
                icon=path,
                icontype='fileicon',
            )
        )

        # Format
        if self.wf.settings.get('use_name', True):
            title = 'Format: Name & Email'
            subtitle = 'Email-only will be used with some problem clients'
        else:
            title = 'Format: Email Only'
            subtitle = 'E.g. bob.smith@example.com'

        if self.wf.settings.get('show_help', True):
            subtitle += help_text

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                valid=True,
                arg='toggle format',
                icon=ICON_CONFIG,
            )
        )

        # Update notification
        if self.wf.settings.get('notify_updates', True):
            title = 'Update Notifications: ON'
            subtitle = 'You will be notifed when a new version is available'
        else:
            title = 'Update Notifications: OFF'
            subtitle = "You will have to check here for a new version"

        if self.wf.settings.get('show_help', True):
            subtitle += help_text

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                valid=True,
                arg='toggle notify_updates',
                icon=ICON_CONFIG,
            )
        )

        # Additional help text in subtitle
        if self.wf.settings.get('show_help', True):
            title = 'Help Text: ON'
            subtitle = 'Action hints will be shown in subtitles'
        else:
            title = 'Help Text: OFF'
            subtitle = 'Subtitles will show no action hints'

        if self.wf.settings.get('show_help', True):
            subtitle += help_text

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                # autocomplete=' {} Format {} '.format(SEPARATOR, SEPARATOR),
                valid=True,
                arg='toggle help_text',
                icon=ICON_CONFIG,
            )
        )

        # Help
        items.append(
            dict(
                title='View MailTo Help',
                subtitle='Open help file in your browser',
                valid=True,
                arg='help',
                icon=ICON_HELP,
            )
        )

        # Filter items if a query was given
        if query:
            items = self.wf.filter(query, items, lambda d: d['title'],
                                   min_score=50)

        # Show error message
        if not items:
            subtitle = 'Try a different query'

            if not self.wf.settings.get('show_help', True):
                subtitle = None

            self.wf.add_item('Nothing matches', subtitle, icon=ICON_WARNING)

        # Send feedback
        for item in items:

            if not self.wf.settings.get('show_help', True):
                item['subtitle'] = None

            self.wf.add_item(**item)

        self.wf.send_feedback()

    #          dP oo                     dP
    #          88                        88
    # .d8888b. 88 dP .d8888b. 88d888b. d8888P
    # 88'  `"" 88 88 88ooood8 88'  `88   88
    # 88.  ... 88 88 88.  ... 88    88   88
    # `88888P' dP dP `88888P' dP    dP   dP

    def choose_client(self, query):
        """Select a new email client"""
        from client import Client
        client = Client()
        log.debug('Choosing email client')
        log.debug('query : {}'.format(query))
        # apps list a list of tuples [(name, path), ...]
        apps = [t for t in client.all_email_apps if os.path.exists(t[1])]

        log.debug('{} email clients on system'.format(len(apps)))

        if not query:  # Show current setting
            if not self.wf.settings.get('default_app'):  # System default
                app = client.system_default_app
                self.wf.add_item(
                    'Current Email Client: System Default',
                    app['path'],
                    icon=app['path'],
                    icontype='fileicon'
                )
            else:  # User has already set a preferred client
                app = client.default_app
                self.wf.add_item(
                    'Current Email Client: {}'.format(app['name']),
                    app['path'],
                    icon=app['path'],
                    icontype='fileicon'
                )
                # Offer to reset
                app = client.system_default_app
                self.wf.add_item(
                    'System Default ({})'.format(app['name']),
                    app['path'],
                    arg='setclient DEFAULT',
                    valid=True,
                    icon=app['path'],
                    icontype='fileicon'
                )

        if query:
            apps = self.wf.filter(query, apps, lambda t: t[0],
                                  min_score=30)

        if not apps:
            self.wf.add_item('Nothing found',
                             'Try another query',
                             icon=ICON_WARNING)

        for name, path in apps:
            arg = 'setclient {}'.format(quote(path))
            # log.debug('arg for `{}` : {}'.format(name, arg))
            self.wf.add_item(name,
                             path,
                             valid=True,
                             arg=arg,
                             icon=path,
                             icontype='fileicon')

        self.wf.send_feedback()

    def do_setclient(self):
        """Change default email client"""
        from client import Client
        client = Client()
        app_path = self.args.query
        log.debug('Setting new client to : {}'.format(app_path))

        if app_path == 'DEFAULT':  # Reset to system default]
            del self.wf.settings['default_app']
            msg = 'Email client set to System Default'
            log.info(msg)
            self.notify(msg)
            return

        if not os.path.exists(app_path):
            msg = "Application doesn't exist : {}".format(app_path)
            self.notify(msg)
            raise ValueError(msg)

        client.default_app = app_path
        msg = 'Email client set to : {}'.format(client.default_app['name'])
        log.info(msg)
        self.notify(msg)

    #   dP                              dP
    #   88                              88
    # d8888P .d8888b. .d8888b. .d8888b. 88 .d8888b. .d8888b.
    #   88   88'  `88 88'  `88 88'  `88 88 88ooood8 Y8ooooo.
    #   88   88.  .88 88.  .88 88.  .88 88 88.  ...       88
    #   dP   `88888P' `8888P88 `8888P88 dP `88888P' `88888P'
    #                      .88      .88
    #                  d8888P   d8888P

    def do_toggle(self):
        """Toggle settings. Dispatch to appropriate method"""
        what = self.args.query
        log.debug('Toggling {} ...'.format(what))

        methname = 'toggle_{}'.format(what)

        if not hasattr(self, methname):
            msg = 'Unknown settings toggle : {!r}'.format(what)
            log.error(msg)
            raise ValueError(msg)

        meth = getattr(self, methname)
        return meth()

    def toggle_format(self):
        """Change format between name+email and email-only"""
        if self.wf.settings.get('use_name', True):
            self.wf.settings['use_name'] = False
            msg = 'Changed format to Email Only'

        else:
            self.wf.settings['use_name'] = True
            msg = 'Changed format to Name & Email'

        log.debug(msg)
        self.notify(msg)

        # Re-open settings
        run_alfred('{} '.format(CONFIG_KEYWORD))

    def toggle_notify_updates(self):
        """Turn update notifications on/off"""
        if self.wf.settings.get('notify_updates', True):
            self.wf.settings['notify_updates'] = False
            msg = 'Turned update notifications off'

        else:
            self.wf.settings['notify_updates'] = True
            msg = 'Turned update notifications on'

        log.debug(msg)
        self.notify(msg)

        # Re-open settings
        run_alfred('{} '.format(CONFIG_KEYWORD))

    def toggle_help_text(self):
        """Turn additional usage notes in subtitles on/off"""
        if self.wf.settings.get('show_help', True):
            self.wf.settings['show_help'] = False
            msg = 'Turned additional help text off'

        else:
            self.wf.settings['show_help'] = True
            msg = 'Turned additional help text on'

        log.debug(msg)
        self.notify(msg)

        # Re-open settings
        run_alfred('{} '.format(CONFIG_KEYWORD))

    # dP     dP           dP
    # 88     88           88
    # 88aaaaa88a .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
    # 88     88  88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
    # 88     88  88.  ... 88 88.  .88 88.  ... 88             88
    # dP     dP  `88888P' dP 88Y888P' `88888P' dP       `88888P'
    #                        88
    #                        dP

    def notify(self, message):
        """Simple wrapper around ``print`` that encodes output"""
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        print(message)

    def _parse_args(self):
        """Parse command-line arguments with argparse"""
        parser = ArgumentParser()
        parser.add_argument(
            'action',
            choices=('search',
                     'config',
                     'setclient',
                     'toggle',
                     'compose',
                     'reload',
                     'update',
                     'help'))
        parser.add_argument('query', nargs='?', default='')
        return parser.parse_args(self.wf.args)


if __name__ == '__main__':
    update_settings = {
        'github_slug': GITHUB_REPO,
        'version': __version__,
        'interval': UPDATE_INTERVAL,
    }

    wf = Workflow(
        update_settings=update_settings,
        default_settings=DEFAULT_SETTINGS,
        # libraries=[os.path.join(os.path.dirname(__file__), 'libs')],
    )
    log = wf.logger
    app = MailToApp()
    sys.exit(wf.run(app.run))
