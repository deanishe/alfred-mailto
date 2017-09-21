#!/usr/bin/python
# encoding: utf-8
#
# Copyright (c) 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-10-03
#

"""Contacts database."""

from __future__ import print_function, unicode_literals, absolute_import

from operator import itemgetter

from workflow import Workflow
from workflow.background import run_in_background, is_running

wf = Workflow()
log = wf.logger


MAX_CACHE_AGE = 3600  # 1 hour
MIN_MATCH_SCORE = 70


class Contacts(object):
    """Simple database of contacts."""

    def __init__(self):
        self.update()

    def update(self, force=False):
        """Load contacts from cache and update cached data if old."""
        # Load cached contacts
        self.contacts = wf.cached_data('contacts', max_age=0)
        if self.contacts is None:
            self.contacts = {}

        # Update if required
        if not wf.cached_data_fresh('contacts', MAX_CACHE_AGE) or force:
            log.debug('Updating contacts cache ...')
            cmd = ['/usr/bin/python', wf.workflowfile('update_contacts.py')]
            run_in_background('update-contacts', cmd)

    @property
    def empty(self):
        return not self.contacts

    @property
    def updating(self):
        return is_running('update-contacts')

    def name_for_email(self, email):
        """Return name associated with email or `None`."""
        key = email.lower()
        contact = self.contacts.get('contacts', {}).get(key)

        if contact:
            log.debug('%r belongs to %r', email, contact['name'])
            return contact['name']

        return None

    def search(self, query):
        """Return list of dicts matching query.

        Dict format:
        {
            'name': 'name of person, company or group',
            'email': 'email',
            'is_group': True/False,
            'is_company': True/False,
        }

        if `group` is True, `email` will be multiple, comma-separated emails

        """
        hits = wf.filter(query, self.contacts['contacts'],
                         itemgetter('key'), min_score=MIN_MATCH_SCORE)

        return hits
