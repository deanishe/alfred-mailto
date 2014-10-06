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
"""

from __future__ import print_function, unicode_literals, absolute_import

from workflow import Workflow
from workflow.background import run_in_background, is_running

wf = Workflow()
log = wf.logger


MAX_CACHE_AGE = 3600  # 1 hour
MIN_MATCH_SCORE = 30


#   ,ad8888ba,
#  d8"'    `"8b                          ,d                            ,d
# d8'                                    88                            88
# 88             ,adPPYba,  8b,dPPYba, MM88MMM ,adPPYYba,  ,adPPYba, MM88MMM ,adPPYba,
# 88            a8"     "8a 88P'   `"8a  88    ""     `Y8 a8"     ""   88    I8[    ""
# Y8,           8b       d8 88       88  88    ,adPPPPP88 8b           88     `"Y8ba,
#  Y8a.    .a8P "8a,   ,a8" 88       88  88,   88,    ,88 "8a,   ,aa   88,   aa    ]8I
#   `"Y8888Y"'   `"YbbdP"'  88       88  "Y888 `"8bbdP"Y8  `"Ybbd8"'   "Y888 `"YbbdP"'

class Contacts(object):

    def __init__(self):
        self.contacts = {}
        self.update()

    #  .d888888   888888ba  dP
    # d8'    88   88    `8b 88
    # 88aaaaa88a a88aaaa8P' 88
    # 88     88   88        88
    # 88     88   88        88
    # 88     88   dP        dP

    def update(self, force=False):
        """Load contacts from cache"""
        # Load cached contacts
        self.contacts = wf.cached_data('contacts', None, max_age=0)

        # Update if required
        if not wf.cached_data_fresh('contacts', MAX_CACHE_AGE) or force:
            log.debug('Updating contacts cache ...')
            cmd = ['/usr/bin/python', wf.workflowfile('update_caches.py')]
            run_in_background('update', cmd)

    @property
    def empty(self):
        return not self.contacts

    @property
    def updating(self):
        return is_running('update')

    def name_for_email(self, email):
        """Return name associated with email or None"""

        s = email.lower()
        for e, name in self.contacts.get('emails', []):
            if s == e.lower():
                log.debug('{} belongs to {}'.format(email, name))
                return name

        return None

    #                                              dP
    #                                              88
    # .d8888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d888b.
    # Y8ooooo. 88ooood8 88'  `88 88'  `88 88'  `"" 88'  `88
    #       88 88.  ... 88.  .88 88       88.  ... 88    88
    # `88888P' `88888P' `88888P8 dP       `88888P' dP    dP

    def search(self, query):
        """Return list of dicts matching query

        Dict format:
        {
            'name': 'name of person or group',
            'email': 'email',
            'group': True/False
        }

        if `group` is True, `email` will be multiple, comma-separated emails

        """

        items = []
        for email, name in self.contacts['emails']:
            items.append({
                'email': email,
                'name': name,
                'group': False
            })

        for name, emails in self.contacts['groups']:
            items.append({
                'name': name,
                'email': ', '.join(emails),
                'group': True
            })

        hits = wf.filter(query, items, self._search_key,
                         min_score=MIN_MATCH_SCORE)

        log.debug('{} hits for `{}`'.format(len(hits), query))
        return hits

    # dP     dP           dP
    # 88     88           88
    # 88aaaaa88a .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
    # 88     88  88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
    # 88     88  88.  ... 88 88.  .88 88.  ... 88             88
    # dP     dP  `88888P' dP 88Y888P' `88888P' dP       `88888P'
    #                        88
    #                        dP

    def _search_key(self, item):
        if item['group']:
            return item['name']

        return '{} {}'.format(item['name'], item['email'])
