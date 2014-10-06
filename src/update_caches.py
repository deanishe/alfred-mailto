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
Read Contacts database and cache relevant information.

Generates a JSON dict:
{
    'names': [
        ['name', ['email1', 'email2', ...]],
        ...
    ],
    'emails': [
        ['email', 'name'],
        ...
    ],
    'groups': [
        ['name', ['email1', 'email2', ...]]
    ]
}
"""

from __future__ import print_function, unicode_literals, absolute_import

import sys
from time import time

import AddressBook as AB

from workflow import Workflow
from client import Client

log = None


#   ,ad8888ba,
#  d8"'    `"8b
# d8'
# 88             ,adPPYba,   ,adPPYba,  ,adPPYba,  ,adPPYYba,
# 88            a8"     "8a a8"     "" a8"     "8a ""     `Y8
# Y8,           8b       d8 8b         8b       d8 ,adPPPPP88
#  Y8a.    .a8P "8a,   ,a8" "8a,   ,aa "8a,   ,a8" 88,    ,88
#   `"Y8888Y"'   `"YbbdP"'   `"Ybbd8"'  `"YbbdP"'  `"8bbdP"Y8
#
#
# 88                     88
# 88                     88
# 88                     88
# 88,dPPYba,   ,adPPYba, 88 8b,dPPYba,   ,adPPYba, 8b,dPPYba, ,adPPYba,
# 88P'    "8a a8P_____88 88 88P'    "8a a8P_____88 88P'   "Y8 I8[    ""
# 88       88 8PP""""""" 88 88       d8 8PP""""""" 88          `"Y8ba,
# 88       88 "8b,   ,aa 88 88b,   ,a8" "8b,   ,aa 88         aa    ]8I
# 88       88  `"Ybbd8"' 88 88`YbbdP"'   `"Ybbd8"' 88         `"YbbdP"'
#                           88
#                           88

def _unwrap(cdw):
    """Return list of objects within a CoreDataWrapper"""
    if not cdw:
        return []
    values = []
    for i in range(cdw.count()):
        values.append(cdw.valueAtIndex_(i))
    return values


def _unicode_list(cdw):
    """Make a list from CoreDataWrapper"""
    return [unicode(v) for v in _unwrap(cdw)]


# map dict keys to AB properties and conversion funcs
_person_text_property_map = {
    # output key :  (property, conversion func)
    'first_name': (AB.kABFirstNameProperty, None),
    'last_name': (AB.kABLastNameProperty, None),
    'company': (AB.kABOrganizationProperty, None),
    'emails': (AB.kABEmailProperty, _unicode_list),
}

#   ,ad8888ba,
#  d8"'    `"8b                                                             ,d
# d8'                                                                       88
# 88             ,adPPYba,  8b,dPPYba,  8b       d8  ,adPPYba, 8b,dPPYba, MM88MMM ,adPPYba, 8b,dPPYba, ,adPPYba,
# 88            a8"     "8a 88P'   `"8a `8b     d8' a8P_____88 88P'   "Y8   88   a8P_____88 88P'   "Y8 I8[    ""
# Y8,           8b       d8 88       88  `8b   d8'  8PP""""""" 88           88   8PP""""""" 88          `"Y8ba,
#  Y8a.    .a8P "8a,   ,a8" 88       88   `8b,d8'   "8b,   ,aa 88           88,  "8b,   ,aa 88         aa    ]8I
#   `"Y8888Y"'   `"YbbdP"'  88       88     "8"      `"Ybbd8"' 88           "Y888 `"Ybbd8"' 88         `"YbbdP"'


def ab_person_to_dict(person):
    """Convert ABPerson to Python dict"""
    d = {}
    d['emails'] = []

    for key in _person_text_property_map:
        prop, func = _person_text_property_map[key]
        value = person.valueForProperty_(prop)
        if func:
            value = func(value)
        if not value:
            value = ''
        d[key] = value

    name = '{} {}'.format(d['first_name'], d['last_name']).strip()
    if not name:
        name = d['company']

    d['name'] = name

    return d


def ab_group_to_dict(group):
    """Convert ABGroup to Python dict. Return None if group is empty"""

    d = {'name': '', 'emails': []}
    d['name'] = group.valueForProperty_(AB.kABGroupNameProperty)

    for person in group.members():
        identifier = group.distributionIdentifierForProperty_person_(
            AB.kABEmailProperty, person)

        if identifier:
            emails = person.valueForProperty_(AB.kABEmailProperty)
            email = emails.valueAtIndex_(emails.indexForIdentifier_(identifier))
            # log.debug('{} is in group {}'.format(email, d['name']))
            d['emails'].append(email)

    if not len(d['emails']):
        return None

    return d

# 88
# 88   ,d                                      ,d
# 88   88                                      88
# 88 MM88MMM ,adPPYba, 8b,dPPYba, ,adPPYYba, MM88MMM ,adPPYba,  8b,dPPYba, ,adPPYba,
# 88   88   a8P_____88 88P'   "Y8 ""     `Y8   88   a8"     "8a 88P'   "Y8 I8[    ""
# 88   88   8PP""""""" 88         ,adPPPPP88   88   8b       d8 88          `"Y8ba,
# 88   88,  "8b,   ,aa 88         88,    ,88   88,  "8a,   ,a8" 88         aa    ]8I
# 88   "Y888 `"Ybbd8"' 88         `"8bbdP"Y8   "Y888 `"YbbdP"'  88         `"YbbdP"'


def iter_people():
    """Yield ABPerson objects for contacts in Address Book"""
    address_book = AB.ABAddressBook.sharedAddressBook()
    for person in address_book.people():
        yield person


def iter_groups():
    """Yield ABGroup objects for groups in Address Book"""
    address_book = AB.ABAddressBook.sharedAddressBook()
    for group in address_book.groups():
        yield group

#                               88
#                               ""

# 88,dPYba,,adPYba,  ,adPPYYba, 88 8b,dPPYba,
# 88P'   "88"    "8a ""     `Y8 88 88P'   `"8a
# 88      88      88 ,adPPPPP88 88 88       88
# 88      88      88 88,    ,88 88 88       88
# 88      88      88 `"8bbdP"Y8 88 88       88


def main(wf):
    start = time()
    contacts = {
        'names': set(),
        'emails': set(),
        'groups': set(),
        # 'email_name': {},
    }

    # Load people

    for person in iter_people():
        person = ab_person_to_dict(person)

        if not len(person['emails']):
            continue

        if person['name']:  # Cache names for email addresses
            for email in person['emails']:
                # contacts['email_name'][email] = person['name']
                contacts['emails'].add((email, person['name']))

        contacts['names'].add((person['name'], tuple(person['emails'])))

        log.debug('{} <{}>'.format(person['name'], person['emails'][0]))

    # Load groups

    for group in iter_groups():
        group = ab_group_to_dict(group)
        if not group:
            continue
        log.debug('Group : "{}"'.format(group['name']))
        contacts['groups'].add((group['name'], tuple(sorted(group['emails']))))

    # Turn sets into lists to make them sortable
    for key in contacts:
        contacts[key] = sorted(list(contacts[key]))

    wf.cache_data('contacts', contacts)

    log.info('{} people, {} groups loaded in {:0.2f} seconds'.format(
             len(contacts['names']), len(contacts['groups']),
             time() - start))

    # Update client application caches
    start = time()
    Client().update()
    log.debug('Client application caches updated in {:0.3f} seconds'.format(
              time() - start))

    return 0


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
