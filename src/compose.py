#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-11-01
#

"""
Compose new email to specified recipients (if any) in selected client.

Client is selected using mailto.py
"""

from __future__ import print_function

import sys
from subprocess import check_call
from urllib import quote

import alfred
from mailto import MailTo
from log import logger

log = logger(u'compose')


def main():
    args = alfred.args()
    log.debug('args : {}'.format(args))
    recipients = []
    mt = MailTo()
    if len(args):
        emails = [s.strip() for s in args[0].split(u',') if s.strip()]
        for email in emails:
            recipients.append(mt.format_recipient(email))
        recipients = u','.join(recipients)
    else:
        recipients = u''
    log.debug(u'args : {}  recipients : {}'.format(args, recipients))
    # build and execute command
    url = u'mailto:{}'.format(quote(recipients))
    log.debug('URL : {}'.format(url))
    appname, path = mt.default_app
    command = [u'open']
    if appname is not None:
        command.append(u'-a')
        command.append(appname)
    command.append(url)
    log.debug(u'command : {}'.format(command))
    retcode = check_call(command)
    return retcode

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as err:
        log.exception(err)
