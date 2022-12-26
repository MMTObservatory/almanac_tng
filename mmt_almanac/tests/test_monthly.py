# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

from ..almanac import monthly_almanac

NGRID = 12


def test_monthly():
    a = monthly_almanac(time="2019-01-01", n_grid_points=NGRID)
    assert len(a) == 31
