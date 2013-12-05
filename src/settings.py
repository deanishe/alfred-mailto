#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2013 deanishe@deanishe.net.
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2013-12-04
#

"""
"""

from __future__ import print_function, unicode_literals

import os
import json
from subprocess import check_output
from time import time

import alfred

version = open(os.path.join(os.path.dirname(__file__), 'version')).read().strip()

class Settings(dict):
    """A dictionary that saves itself when it's changed"""

    log_path = os.path.join(alfred.work(True), u'debug.log')
    handler_plist_path = os.path.expanduser('~/Library/Preferences/com.apple.LaunchServices.plist')
    settings_path = os.path.join(alfred.work(False), u'settings.v-{}.json'.format(version))
    logging_default = False  # logging off by default

    default_settings = {
        'system_default_app' : None,
        'system_default_last_update' : 0,
        'default_app': [None, None],
        'use_name': True,
        'logging': logging_default
    }

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)
        self._nosave = False
        if not os.path.exists(self.settings_path):
            for key, val in self.default_settings.items():
                self[key] = val
            self._save()  # save default settings
        else:
            self._load()

    def _load(self):
        self._nosave = True
        with open(self.settings_path, 'rb') as file:
            for key, value in json.load(file).items():
                self[key] = value
        self._nosave = False
        if (not self.get('system_default_app') or
                os.stat(self.handler_plist_path).st_mtime >
                self['system_default_last_update']):
            self['system_default_app'] = self._get_system_default_client()
            self['system_default_last_update'] = time()

    def _save(self):
        if self._nosave:
            return
        data = {}
        for key, value in self.items():
            data[key] = value
        with open(self.settings_path, 'wb') as file:
            json.dump(data, file, sort_keys=True, indent=2, encoding='utf-8')

    def _get_system_default_client(self):
        command = ['plutil', '-convert', 'json', '-o', '-',
                   self.handler_plist_path]
        d = json.loads(check_output(command))
        for h in d['LSHandlers']:
            if not h.get('LSHandlerURLScheme') == 'mailto':
                continue
            return h['LSHandlerRoleAll']
        return None

    # dict methods
    def __setitem__(self, key, value):
        super(Settings, self).__setitem__(key, value)
        self._save()

    def update(self, *args, **kwargs):
        super(Settings, self).update(*args, **kwargs)
        self._save()

    def setdefault(self, key, value=None):
        super(Settings, self).setdefault(key, value)
        self._save()

if __name__ == '__main__':
    s = Settings()
    for k,v in s.items():
        print('{}  :  {}'.format(k, v))
