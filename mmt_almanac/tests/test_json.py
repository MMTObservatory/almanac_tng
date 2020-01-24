# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import nightly_almanac
from ..json import json_night


def test_json_night():
    a = nightly_almanac(time="2019-01-01")
    s = json_night(almanac=a)
    assert(len(s) > 1)
    s = json_night(almanac=a, pretty=True)
    assert(len(s) > 1)
