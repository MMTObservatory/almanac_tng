# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import monthly_almanac
from ..ascii import ascii_night


def test_ascii_night():
    alms = monthly_almanac(time="2019-01-15")
    for a in alms:
        s = ascii_night(almanac=a)
        assert(len(s) > 1)
