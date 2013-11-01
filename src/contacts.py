#!/usr/bin/env python
# encoding: utf-8

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


def load_from_db_old(dbpath):
    """Return set of tuples (email, name) from specified DB

    `name` may be an empty string.
    """
    contacts = {}  # email : name where name may be u''
    id_name_map = {}
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()

    # Get contact names and IDs
    rows = c.execute(u'SELECT z_pk,zfirstname,zlastname,zorganization,zdisplayflags FROM ZABCDRECORD').fetchall()
    for row in rows:
        id_, firstname, lastname, org, isorg = row
        if firstname is None:
            firstname = u''
        if lastname is None:
            lastname = u''
        if isorg == 1:  # Is a company, not a person
            name = org
        else:
            name = u'{} {}'.format(firstname, lastname).strip()
        if name:
            id_name_map[id_] = name

    # Get email addresses
    rows = c.execute(u'SELECT zaddressnormalized,zowner FROM ZABCDEMAILADDRESS').fetchall()
    for row in rows:
        email, owner = row
        name = id_name_map.get(owner, None)
        if not name and email not in contacts:
            # print(email)
            contacts[email] = u''
        else:
            # print(u'{} <{}>'.format(name, email).encode(u'utf-8'))
            contacts[email] = name

    return contacts

def load_from_db(dbpath):
    """Load contacts and groups from specified DB

    Returns:
        tuple (contacts, groups)
        contacts : dict(email=name)
        groups : dict(name=emails_string)
    """
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()

    # people
    email_id_address_map = {}
    person_id_email_map = defaultdict(list)

    rows = c.execute("SELECT ZABCDEMAILADDRESS.z_pk, zaddressnormalized, zisprimary, zorderingindex, ZABCDRECORD.z_pk, zfirstname, zlastname FROM ZABCDRECORD, ZABCDEMAILADDRESS WHERE ZABCDRECORD.z_ent = 19 AND ZABCDRECORD.z_pk = ZABCDEMAILADDRESS.zowner AND zaddressnormalized != ''").fetchall()
    contacts = {}
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
        contacts[email] = name

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

    groups2 = {}
    for group_id, emails in groups.items():
        name = group_id_name_map[group_id]
        groups2[name] = u', '.join(emails)

    return contacts, groups2


def get_contacts():
    """Return tuple (contacts, groups)

    Loads contacts from cache if it exists and was updated less than
    MAX_CACHE_AGE seconds ago.

    Returns:
        tuple (contacts, groups)
        contacts : list of tuples (email, name)
        groups : list of tuples (name, emails_string)
    """
    if os.path.exists(CACHEPATH) and (time() - os.stat(CACHEPATH).st_mtime) < MAX_CACHE_AGE:
        with open(CACHEPATH) as file:
            data = json.load(file)
            return data[u'contacts'], data[u'groups']
    contacts = {}
    groups = {}
    for dbpath in iter_addressbooks():
        contacts1, groups1 = load_from_db(dbpath)
        for email in contacts1:
            if contacts.get(email, u'') == u'':
                contacts[email] = contacts1[email]
        for name in groups1:
            if groups.get(name, u'') == u'':
                groups[name] = groups1[name]
    contacts = sorted(contacts.items())
    groups = sorted(groups.items())
    with open(CACHEPATH, u'wb') as file:
        json.dump(dict(contacts=contacts, groups=groups), file)
    return contacts, groups
