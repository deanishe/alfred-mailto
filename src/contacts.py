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
Load list of (email, name) contacts from local Contacts/AddressBook
database files on Mac.

Loads local DB first and then iCloud DBs, newest first.
"""

from __future__ import print_function

import sys
import os
import json
import sqlite3
from collections import defaultdict
from time import time

import alfred
from log import logger

log = logger(u'contacts')

LOCAL_CONTACTS_DB = os.path.expanduser(u'~/Library/Application Support/AddressBook/AddressBook-v22.abcddb')
ADDRESSBOOK_DATADIR = os.path.expanduser(u'~/Library/Application Support/AddressBook/Sources')
MAX_DB_COUNT = 3  # number of addressbook files to read
MAX_CACHE_AGE = 600  # 10 minutes

CACHEPATH = os.path.join(alfred.work(True), u'contacts.json')

def iter_addressbooks(limit=MAX_DB_COUNT):
    """
    Return `limit` newest addressbook DBs from tree under `dirpath`
    """
    t = time()
    yield LOCAL_CONTACTS_DB
    paths = []
    for filename in os.listdir(ADDRESSBOOK_DATADIR):
        path = os.path.join(ADDRESSBOOK_DATADIR, filename)
        if not os.path.isdir(path):
            continue
        dbpath = os.path.join(path, u'AddressBook-v22.abcddb')
        if os.path.exists(dbpath):
            paths.append((os.stat(dbpath).st_mtime, dbpath))
    paths.sort(reverse=True)  # newest first
    for i, path in enumerate(paths):
        if i == limit - 1:
            break
        yield paths[i][1]


def load_from_db(dbpath):
    """Load contacts and groups from specified DB

    Returns:
        tuple (email_to_name, name_to_email, groupname_to_email)
        email_to_name : dict[email] = name
        name_to_email : dict[name] = [(primary, order, email), ...]
        groupname_to_email : dict[name] = email
        groups : dict(name=emails_string)
    """
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()

    # people
    email_id_address_map = {}
    email_name_map = {}
    name_emails_map = defaultdict(list)
    person_id_email_map = defaultdict(list)

    rows = c.execute("SELECT ZABCDEMAILADDRESS.z_pk, zaddressnormalized, zisprimary, zorderingindex, ZABCDRECORD.z_pk, zfirstname, zlastname FROM ZABCDRECORD, ZABCDEMAILADDRESS WHERE ZABCDRECORD.z_ent = 19 AND ZABCDRECORD.z_pk = ZABCDEMAILADDRESS.zowner AND zaddressnormalized != ''").fetchall()
    for row in rows:
        email_id, email, primary, order, person_id, first, last = row
        email_id_address_map[email_id] = email
        if primary == 1:
            primary = 0  # so it comes first after sorting
        else:
            primary = 1
        person_id_email_map[person_id].append((primary, order, email))
        if not first:
            first = u''
        if not last:
            last = u''
        name = u'{} {}'.format(first, last).strip()
        if not name:
            name = email
        email_name_map[email] = name
        name_emails_map[name].append((primary, order, email))

    groups = defaultdict(list)
    group_person_email_map = {}
    group_id_name_map = {}

    # specific email addresses for groups
    rows = c.execute("SELECT zcontact, zemail, zgroup FROM ZABCDDISTRIBUTIONLISTCONFIG").fetchall()
    for row in rows:
        person_id, email_id, group_id = row
        group_person_email_map[u'{}-{}'.format(group_id, person_id)] = email_id

    rows = c.execute("SELECT z_pk, zname, z_19contacts FROM ZABCDRECORD, Z_19PARENTGROUPS WHERE z_ent = 15 AND z_15parentgroups1 = z_pk").fetchall()
    for row in rows:
        group_id, name, person_id = row
        if name == u'card':  # contains all contacts
            continue
        # print(row)
        if group_id not in group_id_name_map:
            group_id_name_map[group_id] = name
        email_id = group_person_email_map.get(u'{}-{}'.format(group_id, person_id))
        if email_id:
            groups[group_id].append(email_id_address_map[email_id])
        else:
            emails = sorted(person_id_email_map.get(person_id, []))
            if emails:
                groups[group_id].append(emails[0][2])

    groupname_email_map = {}
    for group_id, emails in groups.items():
        name = group_id_name_map[group_id]
        groupname_email_map[name] = u', '.join(emails)

    return email_name_map, name_emails_map, groupname_email_map


def get_contacts():
    """Return tuple (contacts, groups)

    Loads contacts from cache if it exists and was updated less than
    MAX_CACHE_AGE seconds ago.

    Returns:
        tuple (emails, names, groups)
        emails : list of tuples (email, name)
        names : list of tuples (name, list(emails))
        groups : list of tuples (name, emails_string)
    """
    if os.path.exists(CACHEPATH) and (time() - os.stat(CACHEPATH).st_mtime) < MAX_CACHE_AGE:
        with open(CACHEPATH) as file:
            data = json.load(file)
            return data[u'emails'], data[u'names'], data[u'groups']
    emails = {}
    names = defaultdict(list)
    name_emails_map = defaultdict(set)
    groups = {}
    for dbpath in iter_addressbooks():
        email_to_name, name_to_emails, groupname_to_email = load_from_db(dbpath)
        for email in email_to_name:
            if emails.get(email, u'') == u'':
                emails[email] = email_to_name[email]

        for name, addrs in name_to_emails.items():
            existing = name_emails_map[name]
            for addr in addrs:
                if addr[2] not in existing:
                    name_emails_map[name].add(addr[2])
                    names[name].append(addr)

        for name in groupname_to_email:
            if groups.get(name, u'') == u'':
                groups[name] = groupname_to_email[name]

    emails = sorted(emails.items())
    groups = sorted(groups.items())
    for name, addresses in names.items():
        names[name] = [t[2] for t in sorted(addresses)]
    names = sorted(names.items())

    with open(CACHEPATH, u'wb') as file:
        json.dump(dict(emails=emails, names=names, groups=groups), file)
    return emails, names, groups
