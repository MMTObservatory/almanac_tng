# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..ascii import ascii_night


def test_ascii_night():
    s = ascii_night()
    assert(len(s) > 1)
