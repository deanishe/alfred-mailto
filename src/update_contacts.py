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
    'contacts': [
        {
            'name': "Person's or company name",  # may be empty
            'email': 'email.address@example.com',
            'nickname': "Contact's nickname",
            'company': "Name of contact's company",
            'is_group': True/False,
            'is_company': True/False,
            'key': nickname + name + email,
        },
        ...
    ],
    'email_name_map': {
        'email.address@example.com': "Person's or company name",
        ...
    }
}
"""

from __future__ import print_function, unicode_literals, absolute_import

import sys
from time import time

import AddressBook as AB

from workflow import Workflow
from client import Client

log = None


#  a88888b.
# d8'   `88
# 88        .d8888b. .d8888b. .d8888b. .d8888b.
# 88        88'  `88 88'  `"" 88'  `88 88'  `88
# Y8.   .88 88.  .88 88.  ... 88.  .88 88.  .88
#  Y88888P' `88888P' `88888P' `88888P' `88888P8
#
# dP                dP
# 88                88
# 88d888b. .d8888b. 88 88d888b. .d8888b. 88d888b. .d8888b.
# 88'  `88 88ooood8 88 88'  `88 88ooood8 88'  `88 Y8ooooo.
# 88    88 88.  ... 88 88.  .88 88.  ... 88             88
# dP    dP `88888P' dP 88Y888P' `88888P' dP       `88888P'
#                      88
#                      dP

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
    'nickname': (AB.kABNicknameProperty, None),
    'company': (AB.kABOrganizationProperty, None),
    'emails': (AB.kABEmailProperty, _unicode_list),
}


# .d8888b. .d8888b. 88d888b. dP   .dP .d8888b. 88d888b. .d8888b. dP .d8888b. 88d888b.
# 88'  `"" 88'  `88 88'  `88 88   d8' 88ooood8 88'  `88 Y8ooooo. 88 88'  `88 88'  `88
# 88.  ... 88.  .88 88    88 88 .88'  88.  ... 88             88 88 88.  .88 88    88
# `88888P' `88888P' dP    dP 8888P'   `88888P' dP       `88888P' dP `88888P' dP    dP

def ab_person_to_dict(person):
    """Convert ABPerson to Python dict"""
    d = {'emails': [], 'is_group': False, 'is_company': False}

    for key in _person_text_property_map:
        prop, func = _person_text_property_map[key]
        value = person.valueForProperty_(prop)
        if func:
            value = func(value)
        if not value:
            value = ''
        d[key] = value

    name = '{} {}'.format(d['first_name'], d['last_name']).strip()
    if not name and d.get('company'):
        # log.debug('first_name : {!r} last_name : {!r}'.format(d['first_name'],
        #                                                       d['last_name']))
        # log.debug('company : {!r}'.format(d['company']))
        name = d['company']
        d['is_company'] = True
        # log.debug('company : {!r}'.format(d))

    d['name'] = name

    if not d.get('company'):
        d['company'] = False

    return d


def ab_group_to_dict(group):
    """Convert ABGroup to Python dict. Return None if group is empty"""

    d = {'name': '', 'emails': [], 'is_group': True, 'is_company': False}
    d['name'] = group.valueForProperty_(AB.kABGroupNameProperty)

    for person in group.members():
        identifier = group.distributionIdentifierForProperty_person_(
            AB.kABEmailProperty, person)

        if identifier:
            emails = person.valueForProperty_(AB.kABEmailProperty)
            email = emails.valueAtIndex_(
                emails.indexForIdentifier_(identifier))
            # log.debug('{} is in group {}'.format(email, d['name']))
            d['emails'].append(email)

    if not len(d['emails']):
        return None

    return d


#                              dP                       dP
#                              88                       88
# .d8888b. .d8888b. 88d888b. d8888P .d8888b. .d8888b. d8888P .d8888b.
# 88'  `"" 88'  `88 88'  `88   88   88'  `88 88'  `""   88   Y8ooooo.
# 88.  ... 88.  .88 88    88   88   88.  .88 88.  ...   88         88
# `88888P' `88888P' dP    dP   dP   `88888P8 `88888P'   dP   `88888P'

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


#                     oo
#
# 88d8b.d8b. .d8888b. dP 88d888b.
# 88'`88'`88 88'  `88 88 88'  `88
# 88  88  88 88.  .88 88 88    88
# dP  dP  dP `88888P8 dP dP    dP

def main(wf):
    start = time()
    # list of contact dicts:
    # [
    #     {'name': 'name of contact/company/group',
    #      'email': 'email address',
    #      'key': 'search key',
    #      'group': True/False,
    #      'company': True/False },
    #      ...
    # ]
    contacts = []
    # Needed by `compose` to reconstruct the recipient
    email_name_map = {}
    # Just for logging stats
    people_count = 0
    group_count = 0

    # Load people
    for person in iter_people():
        person = ab_person_to_dict(person)

        if not len(person['emails']):
            continue

        if person['name']:  # Cache names for email addresses
            for email in person['emails']:
                # contacts['email_name'][email] = person['name']
                email_name_map[email] = person['name']

        for email in person['emails']:
            d = {}
            d['name'] = person.get('name')
            d['email'] = email
            d['nickname'] = person.get('nickname')
            d['is_group'] = person.get('group', False)
            d['company'] = person.get('company')
            d['is_company'] = person.get('is_company', False)
            d['key'] = '{} {} {}'.format(d['nickname'], d['name'], d['email'])

            msg = '{} <{}>'.format(d['name'], d['email'])
            if d['nickname']:
                msg += ' ({})'.format(d['nickname'])
            log.debug(msg)
            contacts.append(d)
            people_count += 1

    # Load groups
    for group in iter_groups():
        group = ab_group_to_dict(group)

        if not group:
            continue

        group['email'] = ', '.join(group['emails'])
        group['key'] = group['name']
        i = len(group['emails'])
        del group['emails']

        log.debug('{:3d} people in "{}"'.format(i, group['name']))
        contacts.append(group)
        group_count += 1

    # Turn sets into lists to make them sortable
    # for key in contacts:
    #     contacts[key] = sorted(list(contacts[key]))

    cache_data = {'contacts': contacts, 'email_name_map': email_name_map}

    wf.cache_data('contacts', cache_data)

    log.info('{} people, {} groups cached in {:0.2f} seconds'.format(
             people_count, group_count, time() - start))

    # Update client application caches
    # start = time()
    # Client().update()
    # log.debug('Client application caches updated in {:0.3f} seconds'.format(
    #           time() - start))

    return 0


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
