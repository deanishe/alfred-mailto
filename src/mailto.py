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
    mailto.py edit_client_rules
    mailto.py setclient <app_path>
    mailto.py toggle (format|notify_updates|help_text|notify_cache_updates)
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
import shutil
import subprocess
import sys

from workflow import Workflow

from common import run_alfred, reveal_in_finder

# Placeholder
log = None

# Very basic (and not strictly correct) email validation
# This will (wrongly) reject valid emails with no TLD, e.g.
# dave@localhost, but my assumption is that they ain't very
# commonly used
email_valid = re.compile(r'[^@]+@[^@]+\.[^@]+').match

# Will be opened in your browser when the help item in configuration
# is actioned
HELP_URL = 'http://www.deanishe.net/alfred-mailto/'

# Alfred keyword to open settings. This is used with the `run_alfred`
# function to re-open the configuration after toggling a setting
CONFIG_KEYWORD = 'mailto'

# Query segment separator
SEPARATOR = '⟩'

# Empty file to create in data directory when v2 of the workflow
# has run.
# This is necessary because the v1 settings/cache data is incompatible
# with v2. If this file doesn't exist, all cache and data files
# will be deleted and the file will be created.
V2_HAS_RUN_FILENAME = 'did_run-v2'

DEFAULT_SETTINGS = {
    'use_name': True,  # Use contact names and emails by default
    'notify_updates': True,  # Show user when a new version is available
    'show_help': True,  # Show help text in subtitles
    'notify_cache_updates': False,  # Show user when cache is updating
}

UPDATE_SETTINGS = {
    'github_slug': 'deanishe/alfred-mailto',
    'interval': 1,  # day(s)
}

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
ICON_ON = 'icons/toggle_on.icns'
ICON_OFF = 'icons/toggle_off.icns'
ICON_RULES = 'icons/rules.icns'
ICON_VERSION_NEW = 'icons/update-available.icns'
ICON_VERSION_OK = 'icons/update-none.icns'
ICON_WARNING = 'icons/warning.icns'


# ooo        ooooo            o8o  oooo  ooooooooooooo
# `88.       .888'            `"'  `888  8'   888   `8
#  888b     d'888   .oooo.   oooo   888       888       .ooooo.
#  8 Y88. .P  888  `P  )88b  `888   888       888      d88' `88b
#  8  `888'   888   .oP"888   888   888       888      888   888
#  8    Y     888  d8(  888   888   888       888      888   888
# o8o        o888o `Y888""8o o888o o888o     o888o     `Y8bod8P'

class MailToApp(object):
    """Main application object

    Instatiated and `run()` method called via `Workflow.run()`.

    The first command line argument (action) is handled by the
    correponding `do_action()` method.

    """

    def __init__(self):
        self.wf = None

    # 88d888b. dP    dP 88d888b.
    # 88'  `88 88    88 88'  `88
    # 88       88.  .88 88    88
    # dP       `88888P' dP    dP

    def run(self, wf):
        self.wf = wf
        # Check if v1 was installed and delete its data if if was
        filepath = wf.datafile(V2_HAS_RUN_FILENAME)
        if not os.path.exists(filepath):
            log.debug('First run of v2. Deleting old data…')
            wf.reset()
            open(filepath, 'wb').write('')

        # Copy client_rules.json.template to <datadir> if it doesn't exist
        self.client_rules_path = wf.datafile('client_rules.json')
        self._create_client_rules()
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
        from client import Client
        client = Client()

        log.debug('Searching contacts')

        query = self.args.query

        self.notify_of_update()
        contacts = self.load_contacts()

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

        if client.empty:
            title, subtitle = ('App cache not yet initialised',
                               'Try again in a few seconds…')
            if not self.wf.settings.get('show_help', True):
                subtitle = None
            self.wf.add_item(title, subtitle, icon=ICON_WARNING)
            self.wf.send_feedback()
            return 0

        # Nothing further to be done with no contacts...
        if contacts.empty:
            self.wf.send_feedback()
            return 0

        # Extract email addresses from query
        query, invalid_emails, existing = self.parse_query(query)

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

            subtitle = None

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
                subtitle += '  //  ⇥ to add, ↩ to add & compose'

            self.wf.add_item(item['name'],
                             subtitle,
                             uid=item['email'],
                             autocomplete=recipients + ', ',
                             valid=True,
                             arg='compose ' + quote(recipients),
                             icon=icon)

        self.wf.send_feedback()
        return

    # ------------------------------------------------------------------
    # Search helper methods
    # ------------------------------------------------------------------

    def load_contacts(self):
        """Load contacts from cache"""
        from contacts import Contacts
        contacts = Contacts()
        warning = None

        if contacts.updating and self.wf.settings.get('notify_cache_updates'):
            self.wf.add_item('Updating contacts …', icon=ICON_RELOAD)

            if contacts.empty:
                warning = ('Contacts not yet cached',
                           'Please wait a second or two')
        elif contacts.empty:
            warning = ('No contacts found',
                       'Please check the log file for problems')

        if warning:
            title, subtitle = warning
            if not self.wf.settings.get('show_help', True):
                subtitle = None

            self.wf.add_item(title, subtitle, icon=ICON_WARNING)

        return contacts

    def parse_query(self, query):
        """Extract existing valid and invalid email addresses from query

        Return current query, invalid addresses and valid addresses
        """
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

        msg = ('existing : {!r} emails : {!r} '
               'invalid_emails : {!r} query : {!r}')
        log.debug(msg.format(existing, emails, invalid_emails, query))

        return (query, invalid_emails, existing)

    def notify_of_update(self):
        """Add notification to results list if newer version available"""
        if self.wf.settings.get('notify_updates', True):
            if self.wf.update_available:
                version = wf.cached_data('__workflow_update_status',
                                         max_age=0)['version']

                subtitle = (
                    '↩ to install new version, '
                    '"{}" to turn off notifications'.format(
                        CONFIG_KEYWORD)
                )

                if not self.wf.settings.get('show_help', True):
                    subtitle = None

                self.wf.add_item(
                    'Version {} is available'.format(version),
                    subtitle,
                    valid=True,
                    arg='update',
                    icon=ICON_VERSION_NEW,
                )

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

    #                dP oo   dP                        dP
    #                88      88                        88
    # .d8888b. .d888b88 dP d8888P    88d888b. dP    dP 88 .d8888b. .d8888b.
    # 88ooood8 88'  `88 88   88      88'  `88 88    88 88 88ooood8 Y8ooooo.
    # 88.  ... 88.  .88 88   88      88       88.  .88 88 88.  ...       88
    # `88888P' `88888P8 dP   dP      dP       `88888P' dP `88888P' `88888P'

    def do_edit_client_rules(self):
        """Open user's `client_rules.json` in Finder"""
        self._create_client_rules()
        reveal_in_finder(self.client_rules_path)
        self.notify('Revealing client rules file in Finder')

    #                   dP                         dP
    #                   88                         88
    # 88d888b. .d8888b. 88 .d8888b. .d8888b. .d888b88
    # 88'  `88 88ooood8 88 88'  `88 88'  `88 88'  `88
    # 88       88.  ... 88 88.  .88 88.  .88 88.  .88
    # dP       `88888P' dP `88888P' `88888P8 `88888P8

    def do_reload(self):
        """Force update of contacts cache"""
        log.debug('Forcing cache update ...')
        from contacts import Contacts
        from client import Client
        Contacts().update(force=True)
        Client().update(force=True)
        self.notify('Refreshing contacts and app caches…')
        run_alfred('{} '.format(CONFIG_KEYWORD))
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
        log.debug('Opening {} in browser ...'.format(HELP_URL))
        subprocess.call(['open', HELP_URL])

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
        log.debug('Showing settings')

        query = self.args.query
        log.debug('query : {}'.format(query))

        # Go back
        # --------------------------------------------------------------
        if query.endswith(SEPARATOR):  # User deleted trailing space
            run_alfred('{} '.format(CONFIG_KEYWORD))
            return

        # Subquery
        # --------------------------------------------------------------
        # Parse subqueries and dispatch to appropriate method
        # A subquery is `keyword + <SEPARATOR> + <space>`
        # `query` will be the rest of the original `query` after
        # the first `<SEPARATOR>`
        if SEPARATOR in query:
            parts = [s.strip() for s in query.split(SEPARATOR) if s.strip()]
            log.debug('parts : {}'.format(parts))

            if parts:
                action = parts[0]
                if len(parts) > 1:
                    query = parts[1]
                else:
                    query = None

                # `Client` is the only subquery at the moment
                if action == 'Client':
                    return self.choose_client(query)
                else:
                    self.wf.add_item('Unknown setting : {}'.format(action),
                                     'Try a different query',
                                     icon=ICON_WARNING)

                    self.wf.send_feedback()
                    return

        # Display root configuration options
        # --------------------------------------------------------------

        items = self.get_config_items()

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

    def get_config_items(self):
        """Return list of all configuration items"""
        from client import Client
        client = Client()
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
                    title='MailTo is up to date (v{})'.format(self.wf.version),
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
                icon=ICON_RELOAD,
            )
        )

        # Notify user when cache is updating
        if self.wf.settings.get('notify_cache_updates'):
            title = 'Notify of cache update: ON'
            subtitle = "'Updating contacts' item will be shown in results"
            icon = ICON_ON
        else:
            title = 'Notify of cache update: OFF'
            subtitle = "'Updating contacts' item will not be shown in results"
            icon = ICON_OFF

        if self.wf.settings.get('show_help', True):
            subtitle += help_text

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                valid=True,
                arg='toggle notify_cache_updates',
                icon=icon,
            )
        )

        # Client
        app = self.wf.settings.get('default_app')

        if app:
            appname = app['name']
            path = app['path']

        else:
            appname = 'System Default'
            path = client.system_default_app.get('path', '')

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
            icon = ICON_ON
            subtitle = 'You will be notifed when a new version is available'
        else:
            title = 'Update Notifications: OFF'
            icon = ICON_OFF
            subtitle = "You will have to check here for a new version manually"

        if self.wf.settings.get('show_help', True):
            subtitle += help_text

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                valid=True,
                arg='toggle notify_updates',
                icon=icon,
            )
        )

        # Additional help text in subtitle
        if self.wf.settings.get('show_help', True):
            title = 'Help Text: ON'
            icon = ICON_ON
            subtitle = 'Action hints will be shown in subtitles' + help_text
        else:
            title = 'Help Text: OFF'
            icon = ICON_OFF
            subtitle = 'Subtitles will show no action hints'

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                # autocomplete=' {} Format {} '.format(SEPARATOR, SEPARATOR),
                valid=True,
                arg='toggle help_text',
                icon=icon,
            )
        )

        # Edit client rules
        title = 'Edit Client Formatting Rules'
        subtitle = 'Override the defaults or configure a new email client'

        if not self.wf.settings.get('show_help', True):
            subtitle = None

        items.append(
            dict(
                title=title,
                subtitle=subtitle,
                # autocomplete=' {} Format {} '.format(SEPARATOR, SEPARATOR),
                valid=True,
                arg='edit_client_rules',
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

        return items

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
        apps = [d for d in client.all_email_apps if os.path.exists(d['path'])]

        log.debug('{} email clients on system'.format(len(apps)))

        if client.empty:
            if not client.updating:
                client.update(force=True)

            self.wf.add_item(
                'Application list is currently empty',
                'Check back in a few seconds after the update has finished',
                icon=ICON_WARNING,
            )
            self.wf.send_feedback()
            return

        if not query:  # Show current setting
            if not self.wf.settings.get('default_app'):  # System default
                app = client.system_default_app
                self.wf.add_item(
                    'Current Email Client: System Default',
                    app['path'],
                    # modifier_subtitles={'cmd': app['bundleid']},
                    icon=app['path'],
                    icontype='fileicon'
                )
            else:  # User has already set a preferred client
                app = client.default_app
                self.wf.add_item(
                    'Current Email Client: {}'.format(app['name']),
                    app['path'],
                    # modifier_subtitles={'cmd': app['bundleid']},
                    icon=app['path'],
                    icontype='fileicon'
                )
                # Offer to reset
                app = client.system_default_app
                self.wf.add_item(
                    'System Default ({})'.format(app['name']),
                    app['path'],
                    modifier_subtitles={'cmd': app['bundleid']},
                    arg='setclient DEFAULT',
                    valid=True,
                    copytext=app['bundleid'],
                    icon=app['path'],
                    icontype='fileicon'
                )

        if query:
            apps = self.wf.filter(query, apps, lambda d: d['name'],
                                  min_score=30)

        if not apps:
            self.wf.add_item('Nothing found',
                             'Try another query',
                             icon=ICON_WARNING)

        for app in apps:
            arg = 'setclient {}'.format(quote(app['path']))
            # log.debug('arg for `{}` : {}'.format(name, arg))
            self.wf.add_item(app['name'],
                             app['path'],
                             modifier_subtitles={'cmd': app['bundleid']},
                             valid=True,
                             copytext=app['bundleid'],
                             arg=arg,
                             icon=app['path'],
                             icontype='fileicon')

        self.wf.send_feedback()

    def do_setclient(self):
        """Change default email client"""
        from client import Client
        client = Client()
        app_path = self.args.query
        log.debug('Setting new client to : {}'.format(app_path))

        if app_path == 'DEFAULT':  # Reset to system default
            del self.wf.settings['default_app']
            msg = 'Email client set to System Default'
            log.info(msg)
            self.notify(msg)
            run_alfred('{} '.format(CONFIG_KEYWORD))
            return

        if not os.path.exists(app_path):
            msg = "Application doesn't exist : {}".format(app_path)
            self.notify(msg)
            raise ValueError(msg)

        client.default_app = app_path
        msg = 'Email client set to : {}'.format(client.default_app['name'])
        log.info(msg)
        self.notify(msg)
        run_alfred('{} '.format(CONFIG_KEYWORD))

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

    def toggle_notify_cache_updates(self):
        """Turn cache update notifications on/off"""
        if self.wf.settings.get('cache_notify_updates', True):
            self.wf.settings['cache_notify_updates'] = False
            msg = 'Turned cache update notifications off'

        else:
            self.wf.settings['cache_notify_updates'] = True
            msg = 'Turned cache update notifications on'

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

    def _create_client_rules(self):
        """Copy `client_rules.json.template` to datadir"""
        if not os.path.exists(self.client_rules_path):
            srcpath = self.wf.workflowfile('client_rules.json.template')
            shutil.copy(srcpath, self.client_rules_path)
            log.debug('Created empty client rules file at {}'.format(
                      self.client_rules_path))

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
                     'edit_client_rules',
                     'setclient',
                     'toggle',
                     'compose',
                     'reload',
                     'update',
                     'help'))
        parser.add_argument('query', nargs='?', default='')
        return parser.parse_args(self.wf.args)


if __name__ == '__main__':

    wf = Workflow(
        update_settings=UPDATE_SETTINGS,
        default_settings=DEFAULT_SETTINGS,
        # libraries=[os.path.join(os.path.dirname(__file__), 'libs')],
    )
    # wf.magic_prefix = 'wf:'
    log = wf.logger
    app = MailToApp()
    sys.exit(wf.run(app.run))
