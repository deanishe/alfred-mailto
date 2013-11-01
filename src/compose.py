#!/usr/bin/env python
# encoding: utf-8

"""
Compose new email to specified recipients (if any) in selected client.

Client is selected using mailto.py
"""

from __future__ import print_function

import sys
import os
from subprocess import check_call

import alfred
from mailto import MailApps
from contacts import get_contacts

# import logging
# logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), u'debug.log'),
#                     level=logging.DEBUG)
# log = logging.getLogger(u'compose')




def main():
    args = alfred.args()
    recipients = []
    if len(args):
        emails = [s.strip() for s in args[0].split(u',') if s.strip()]
        contacts = dict(get_contacts()[0])  # email : name
        for email in emails:
            name = contacts.get(email)
            if name and name != email:
                recipients.append(u'{} <{}>'.format(name, email))
            else:
                log.debug(u'Not found : {}'.format(email))
                recipients.append(email)
        recipients = u','.join(recipients)
    else:
        recipients = u''
    # log.debug(u'args : {}  recipients : {}'.format(args, recipients))
    # build and execute command
    url = u'mailto:{}'.format(recipients)
    appname, path = MailApps().default_app

    command = [u'open']
    if appname is not None:
        command.append(u'-a')
        command.append(appname)
    command.append(url)
    # log.debug(u'command : {}'.format(command))
    retcode = check_call(command)
    return retcode

if __name__ == '__main__':
    sys.exit(main())
