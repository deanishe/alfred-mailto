#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""
Select email addresses from your contacts/enter them manually and send
them to your preferred mail client (via compose.py and mailto.py)

TODO: allow sending when there is just a trailing comma and space
TODO: fix multiple recipients to mail client
"""

from __future__ import print_function

import sys
import os
from email.utils import formataddr
import re

from contacts import get_contacts
import alfred
from mailto import MailTo

# import logging
# logging.basicConfig(filename=os.path.join(alfred.work(True), u'debug.log'),
#                     level=logging.DEBUG)
# log = logging.getLogger(u'search')

MAX_RESULTS = 50
KEYWORDS = [u'getdefault', u'setdefault', u'cleardefault', u'help',
            u'format', u'usename']

valid_email = re.compile(r'[^@]+@[^@]+\.[^@]+').match


def main():
    args = alfred.args()
    if len(args):
        q = args[0].lstrip(u', ').strip()
    else:
        q = u''

    # log.debug(u'args : {} q : {!r}'.format(args, q))

    if q == u'':  # Compose empty mail
        item = alfred.Item(
            {u'valid':u'yes',
            u'arg':u'',
            u'uid':u'compose'},
            u'Write new email',
            u'Hit ENTER to compose a new mail or start typing to add recipients',
            icon=u'icon.png'
        )
        xml = alfred.xml([item])
        # log.debug(xml)
        print(xml)
        return 0


    # Split out existing valid and invalid recipients
    q = q.lower()
    existing = u''
    addresses = []
    invalid_addresses = []
    if u',' in q:
        addresses = [s.strip() for s in q.split(u',')]
        if len(addresses):
            existing = []
            for email in addresses[:-1]:
                if not valid_email(email):
                    invalid_addresses.append(email)
                else:
                    existing.append(email)
            if len(existing):
                existing = u', '.join(existing) + u', '
            else:
                existing = u''
            q = addresses[-1]

    # log.debug(u'args : {}, existing : {}  addresses : {} invalid_addresses : {} q : {!r}'.format(args, existing, addresses, invalid_addresses, q))


    contacts = []
    hits = []
    items = []

    if q != u'':
        # Find matching contacts
        email_to_name, name_to_email, groups = get_contacts()

        # startswith
        # group names
        for name, email in groups:
            if name.lower().startswith(q) and (name, email) not in hits:
                hits.append((name, email))
        # contact names
        for name, emails in name_to_email:
            if name.lower().startswith(q):
                for email in emails:
                    if (name, email) not in hits:
                        hits.append((name, email))
        # for email, name in email_to_name:
        #     if name.lower().startswith(q):
        #         hits.append((name, email))
        # email addresses
        for email, name in email_to_name:
            if email.lower().startswith(q) and (name, email) not in hits:
                hits.append((name, email))

        # search in

        # groups
        for name, email in groups:
            if q in name.lower() and (name, email) not in hits:
                hits.append((name, email))
        # contact names
        for name, emails in name_to_email:
            if q in name.lower():
                for email in emails:
                    if (name, email) not in hits:
                        hits.append((name, email))
        # email addresses
        for email, name in email_to_name:
            if q in email.lower() and (name, email) not in hits:
                hits.append((name, email))


    # show errors first
    for email in invalid_addresses:
        item = alfred.Item(
            {u'valid':u'no'},
            u'{} is not a valid email address'.format(email),
            u'Try something else',
            icon=u'warning.png'
        )
        items.append(item)

    # q does not match anything
    if not len(hits):
        if valid_email(q) or (q == u'' and existing != u''):
            recipients = (existing + q).rstrip(u', ')
            item = alfred.Item(
                {u'valid':u'yes',
                u'arg':recipients},
                u'Write mail to {}'.format(recipients),
                u'Hit ENTER to compose a new message',
                icon=u'icon.png'
            )
            items.append(item)
        elif q != u'' and q not in KEYWORDS:  # show error and offer to mail existing recipients
            item = alfred.Item(
                {u'valid':u'no'},
                u'{} is not a valid email address'.format(q),
                u'Try something else',
                icon=u'warning.png'
            )
            items.append(item)
            if existing:
                recipients = existing.rstrip(u', ')
                item = alfred.Item(
                    {u'valid':u'yes',
                    u'arg':recipients},
                    u'Write mail to {}'.format(recipients),
                    u'Hit ENTER to compose a new message',
                    icon=u'icon.png'
                )
                items.append(item)
        xml = alfred.xml(items)
        print(xml)
        return 0

    # got some matches, show them
    for name, email in hits:
        if email in addresses:
            continue
        if u', ' in email:  # is a group
            icon = u'group.png'
        else:
            icon = u'icon.png'
        recipients = existing + email + u', '
        item = alfred.Item(
            {u'valid':u'yes',
            u'arg':recipients,
            u'uid':recipients,
            u'autocomplete':recipients},
            name,
            email,
            icon=icon
        )
        items.append(item)

    if not len(items):  # all results are in existing recipients, compose message to nobody
        recipients = existing + email + u', '
        item = alfred.Item(
            {u'valid':u'yes',
            u'arg':recipients,
            u'autocomplete':recipients},
            u'Write mail to {}'.format(recipients),
            u'Hit ENTER to compose a new message',
            icon=u'icon.png'
        )
        items.append(item)
    xml = alfred.xml(items, maxresults=MAX_RESULTS)
    print(xml)
    return 0

if __name__ == '__main__':
    sys.exit(main())