#!/usr/bin/env python
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

import sys
import os
import unittest


if os.path.abspath(os.curdir) != os.path.abspath(os.path.dirname(__file__)):
    print('You must run the test script from the workflow directory (src)')
    sys.exit(1)

from settings import Settings


class TestSettings(unittest.TestCase):

    test_settings_path = os.path.join(os.path.dirname(__file__), 'test_settings.json')

    def setUp(self):
        Settings.settings_path = self.test_settings_path

    def tearDown(self):
        if os.path.exists(self.test_settings_path):
            os.unlink(self.test_settings_path)

    def test_settings_load(self):
        self.assertFalse(os.path.exists(self.test_settings_path))
        s = Settings()
        for key, value in s.default_settings.items():
            self.assert_(s[key] == value)
            self.assert_(s.get(key) == value)
        self.assert_(os.path.exists(s.settings_path))

    def test_settings_save(self):
        s = Settings()
        for key in s.default_settings:
            self.assert_(s[key] == s.default_settings[key])
        s['test_value'] = 1
        s1 = Settings()
        self.assert_(s1.get('test_value') == 1)
        self.assert_(s1['test_value'] == 1)


if __name__ == '__main__':
    unittest.main()
