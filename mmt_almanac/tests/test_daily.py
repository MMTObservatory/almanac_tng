# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import nightly_almanac

def test_nightly():
    a = nightly_almanac(time="2019-01-01")
    assert(len(list(a.keys())) > 1)
