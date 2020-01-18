# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import nightly_almanac
from ..ascii import ascii_night


def test_ascii_night():
    a = nightly_almanac(time="2019-01-01")
    s = ascii_night(almanac=a)
    assert(len(s) > 1)
