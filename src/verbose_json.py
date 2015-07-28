#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-10-18
#

"""
Wrapper around `json` module to strip comments
"""

from __future__ import print_function, unicode_literals, absolute_import

import json
from cStringIO import StringIO


def load(fp, *args, **kwargs):
    real_json = []
    in_multiline_comment = False
    for line in fp:
        l = line.strip()
        if l.startswith(b'//'):
            continue
        if l.startswith(b'/*'):
            in_multiline_comment = True
            continue
        if l.startswith(b'*/'):
            in_multiline_comment = False
            continue
        if in_multiline_comment:
            continue
        real_json.append(line)

    sio = StringIO(b'\n'.join(real_json))
    return json.load(sio, *args, **kwargs)


def dump(fp, *args, **kwargs):
    return json.dump(fp, *args, **kwargs)
