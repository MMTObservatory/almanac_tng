# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import monthly_almanac

def test_monthly():
    a = monthly_almanac(time="2019-01-01")
    assert(len(list(a.keys())) == 31)
