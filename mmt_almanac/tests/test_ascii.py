# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8
import argparse
from unittest import mock

from ..ascii import ascii_night, ascii_month, ascii_year, yearly_almanac


def test_ascii_night():
    s = ascii_night()
    assert len(s) > 1


def test_ascii_month():
    s = ascii_month()
    assert len(s) > 1


def test_ascii_year():
    s = ascii_year()
    assert len(s) > 1


@mock.patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(outfile='almanac.txt', year=2021))
def test_yearly_almanac(mock_args):
    yearly_almanac()
    with open("almanac.txt", 'r') as fp:
        s = fp.read()
    assert len(s) > 1
