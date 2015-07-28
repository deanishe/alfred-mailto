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
"""

from __future__ import print_function, unicode_literals, absolute_import


import os
import subprocess

from workflow import Workflow

wf = Workflow()
log = wf.logger

ONE_DAY = 86400
ONE_HOUR = 3600
ONE_WEEK = ONE_DAY * 7
ONE_MONTH = ONE_DAY * 30
ALFRED_SCRIPT = 'tell application "Alfred 2" to search "{}"'
REVEAL_SCRIPT = '''
tell application "Finder"
    reveal POSIX file "{}"
    activate
end tell
'''


def _applescriptify(text):
    """Replace double quotes in text"""
    return text.replace('"', '" + quote + "')


def appname(app_path):
    """Return app name for application at ``app_path``"""
    return os.path.splitext(os.path.basename(app_path))[0]


def bundleid(app_path):
    """Return bundle ID for application at ``app_path``"""
    from Foundation import NSBundle
    bundle = NSBundle.bundleWithPath_(app_path)
    return bundle.bundleIdentifier()


def nsurl_to_path(nsurl):
    """Convert a file:// NSURL object to a Unicode path"""
    return wf.decode(nsurl.path()).rstrip('/')


def reveal_in_finder(path):
    """Tell Finder to show file at path"""
    cmd = ['/usr/bin/osascript', '-e',
           REVEAL_SCRIPT.format(_applescriptify(path))]
    log.debug('Running command : {}'.format(cmd))
    command_output(cmd)


def run_alfred(query):
    """Run Alfred with ``query`` via AppleScript"""
    script = ALFRED_SCRIPT.format(_applescriptify(query))
    log.debug('calling Alfred with : {!r}'.format(script))
    return subprocess.call(['osascript', '-e', script])


def command_output(cmd):
    """Wraps :func:`subprocess.check_output` and decode output"""
    log.debug('Running command : {}'.format(cmd))
    return wf.decode(subprocess.check_output(cmd)).strip()


def command_lines(cmd):
    """Return results of :func:`command_output` as a list of lines"""
    log.debug('Running command : {}'.format(cmd))
    return [s.strip() for s in command_output(cmd).split('\n') if s.strip()]
