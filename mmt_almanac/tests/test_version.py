# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

import mmt_almanac


def test_version():
    ver = mmt_almanac.__version__
    assert(len(ver) > 1)
