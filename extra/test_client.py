#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-12-05
#

"""test_client [-h|--help] <client>

Call specified client with a series of mailto: URLs to test support

Usage:
    test_client <client>
    test_client (-h|--help)

Options:
    -h, --help  Show this help message.
"""

from __future__ import print_function  #, unicode_literals


from subprocess import check_call
from time import sleep
from email.header import Header
from urllib import quote
import docopt

contacts = [
    ('Bob Test', 'bob@deanishe.net'),
    ('Sue Test', 'sue@deanishe.net'),
    ('Dave Test', 'dave@deanishe.net'),
    ('Jürgen Probe', 'probi@deanishe.net'),
    ('Probe, Heinrich, Dr.', 'heini@deanishe.net'),
    ('Harry Test — Splendid, Inc.', 'harry@deanishe.net')
]

WAIT_FOR = 5  # seconds

URLS = [

('Name, email, space, MIME-encoded, URL-quoted', 'mailto:?to=Bob%20Test%20%3Cbob%40example.com%3E%2C%20Sue%20Test%20%3Csue%40example.com%3E%2C%20Dave%20Test%20%3Cdave%40example.com%3E%2C%20%3D%3Futf-8%3Fq%3FJ%3DC3%3DBCrgen_Probe%3F%3D%20%3Cprobi%40example.com%3E%2C%20%22Probe%2C%20Heinrich%2C%20Dr.%22%20%3Cheini%40example.com%3E%2C%20%3D%3Futf-8%3Fb%3FIkhhcnJ5IFRlc3Qg4oCUIFNwbGVuZGlkLCBJbmMuIg%3D%3D%3F%3D%20%3Charry%40example.com%3E&subject=Name%20%26%20email%2C%20with%20space%2C%20MIME-encoded%2C%20URL-quoted'),  # default (Mail, MailMate, Thunderbird)
('Email-only, no space', 'mailto:?to=bob@example.com,sue@example.com,dave@example.com,probi@example.com,heini@example.com,harry@example.com&subject=Email%20only%2C%20no%20space'),  # Airmail
('Name, email, space. Email-only if commas', 'mailto:?to=Bob Test <bob@example.com>,Sue Test <sue@example.com>,Dave Test <dave@example.com>,Jürgen Probe <probi@example.com>,heini@example.com,harry@example.com&subject=Name &amp; email, no space, email only if commas'),  # Unibox
('Name, email, space. Quotes for commas', 'mailto:?to=Bob Test <bob@example.com>, Sue Test <sue@example.com>, Dave Test <dave@example.com>, Jürgen Probe <probi@example.com>, "Probe, Heinrich, Dr." <heini@example.com>, "Harry Test — Splendid, Inc." <harry@example.com>&subject=Name%20%26%20email%2C%20with%20space%2C%20MIME-encoded%2C%20URL-quoted')  # Sparrow
]


def encode(s):
    return Header(s, charset='utf-8')


def enquoten(s):
    if ',' in s:
        return '"{}"'.format(s)
    return s


def open_url(client, url):
    print(url)
    check_call(['open', '-a', client, url])
    print('')
    return did_it_work()
    # sleep(WAIT_FOR)


def build_url(to, subject):
    print('')
    print(subject)
    # return 'mailto:{}?subject={}'.format(to, subject.replace('&', 'and'))
    return 'mailto:?to={}&subject={}'.format(to, subject.replace('&', 'and'))


def did_it_work():
    response = None
    while response not in ('y', 'n'):
        response = raw_input('Did it work? [y/n] ').lower()

    return response == 'y'


def main():
    args = docopt.docopt(__doc__)
    client = args.get('<client>')
    results = []
    print("Testing client '{}' ...".format(client))

    if True:
        title = 'Email only, no space'
        parts = [email for (name, email) in contacts]
        url = build_url(','.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Email only, with space'
        parts = [email for (name, email) in contacts]
        url = build_url(', '.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Name & email, quoted, no space'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(','.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Name & email, quoted, with space'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(', '.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Name & email, no space, MIME-encoded'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            name = encode(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(','.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Name & email, with space, MIME-encoded'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            name = encode(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(', '.join(parts), title)
        results.append((title, open_url(client, url)))

        title = 'Name & email, no space, MIME-encoded, URL-encoded'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            name = encode(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(quote(','.join(parts)), quote(title))
        results.append((title, open_url(client, url)))

    if False:
        title = 'Name & email, with space, MIME-encoded, URL-encoded'
        parts = []
        for name, email in contacts:
            name = enquoten(name)
            # name = encode(name)
            parts.append('{} <{}>'.format(name, email))
        url = build_url(', '.join(parts), quote(title))
        results.append((title, open_url(client, url)))

    if True:
        title = 'Name & email, no space, email only if commas'
        parts = []
        for name, email in contacts:
            if ',' in name:
                parts.append(email)
            else:
                # name = enquoten(name)
                # name = encode(name)
                parts.append('{} <{}>'.format(name, email))
        url = build_url(','.join(parts), title)
        results.append((title, open_url(client, url)))

    if False:

        for title, url in URLS:
            print(title)
            print('{!r}'.format(url))
            open_url(client, url)
            results.append((title, did_it_work()))

    print('\n\nResults for {}:'.format(client))

    for (title, success) in results:
        print('\t{:5s} : {}'.format(str(success), title))

if __name__ == '__main__':
    main()
