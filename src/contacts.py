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
    for i in range(limit - 1):
        yield paths[i][1]


def load_from_db(dbpath):
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


def get_contacts():
    """Return list of (email, name) tuples

    Loads contacts from cache if it exists and was updated less than
    MAX_CACHE_AGE seconds ago.
    """
    if os.path.exists(CACHEPATH) and (time() - os.stat(CACHEPATH).st_mtime) < MAX_CACHE_AGE:
        with open(CACHEPATH) as file:
            return json.load(file)
    contacts = {}
    for dbpath in iter_addressbooks():
        result = load_from_db(dbpath)
        for email in result:
            if contacts.get(email, u'') == u'':
                contacts[email] = result[email]
    contacts = sorted(contacts.items())
    with open(CACHEPATH, u'wb') as file:
        json.dump(contacts, file)
    return contacts
