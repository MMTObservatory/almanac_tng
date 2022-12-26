# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import nightly_almanac

NGRID = 12


def test_nightly():
    a = nightly_almanac(time="2019-01-01", n_grid_points=NGRID)
    assert len(list(a.keys())) > 1
