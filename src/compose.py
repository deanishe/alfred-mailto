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

# import logging
# logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), u'log.log'),
#                     level=logging.DEBUG)
# log = logging.getLogger(u'compose')

def main():
    args = alfred.args()
    if len(args):
        recipients = args[0].strip()
    else:
        recipients = u''
    recipients = recipients.replace(u', ', u',')
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
