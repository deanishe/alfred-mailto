#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-10-18
#

"""Update cache of all apps on system that can handle mailto: URIs."""

from __future__ import print_function, unicode_literals, absolute_import


import sys
from time import time


from LaunchServices import (LSCopyApplicationURLsForURL,
                            LSGetApplicationForURL,
                            kLSRolesAll,
                            CFURLCreateWithString)

from workflow import Workflow
from common import nsurl_to_path, appname, bundleid

wf = Workflow()
log = wf.logger


def get_email_handlers():
    """Find all apps that can handle mailto URLs"""

    url = CFURLCreateWithString(None, 'mailto:test@example.com', None)
    apps = {}

    nsurls = LSCopyApplicationURLsForURL(url, kLSRolesAll)
    paths = set([nsurl_to_path(nsurl) for nsurl in nsurls])

    for path in paths:
        app = {'path': path}
        app['name'] = appname(path)
        app['bundleid'] = bundleid(path)
        apps[app['bundleid']] = app
        log.debug('mailto handler : {} // {}'.format(
                  app['bundleid'], app['path']))

    apps = sorted(apps.values(), key=lambda d: d['name'])

    log.debug('{} email clients found'.format(len(apps)))

    return apps


def get_system_default_handler():
    """Return app info for system default mailto handler"""
    url = CFURLCreateWithString(None, 'mailto:test@example.com', None)
    app = {}
    ok, info, nsurl = LSGetApplicationForURL(url, kLSRolesAll,
                                             None, None)

    app['path'] = nsurl_to_path(nsurl)
    app['name'] = appname(app['path'])
    app['bundleid'] = bundleid(app['path'])

    log.debug('System default mailto handler : {}'.format(app))
    return app


def main(wf):
    start_time = time()
    wf.cache_data('system_default_app', get_system_default_handler())
    wf.cache_data('all_apps', get_email_handlers())
    log.debug('Client application caches updated in {:0.3f} seconds'.format(
              time() - start_time))


if __name__ == '__main__':
    sys.exit(wf.run(main))
