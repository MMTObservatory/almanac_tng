# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import yearly_almanac


def test_yearly():
    a = yearly_almanac(year=2020)
    assert(len(list(a.keys())) == 12)
