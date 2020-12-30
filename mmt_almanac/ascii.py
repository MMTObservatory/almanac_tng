# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

import pkg_resources
import datetime

import multiprocessing
from multiprocessing import Pool

import pandas as pd

from astropy.time import Time
import astropy.units as u
from skyfield import almanac

from .almanac import nightly_almanac, TZ, HORIZONS


HM_STR = "%-H %M"

TBL_HDR = "     {:4d}          Sun     Sun     Sun    RA 3H                RA 3H    Sun     Sun     Sun               Moon    Moon   Moon at Midnight\n"  # noqa
TBL_HDR += " Date    Sunset   6 Deg   12 Deg  18 Deg  West at  Sid Time    East at 18 Deg  12 Deg  6 Deg  Sunrise     rise    set    Illum     Age  \n"  # noqa
TBL_HDR += "                  W Hrz   W Hrz   W Hrz   18 Deg   Midnight    18 Deg  E Hrz   E Hrz   E Hrz                               %       Days\n"  # noqa

PAGE_HDR_FILE = pkg_resources.resource_filename(__name__, "header.txt")


def nearest_minute(dt):
    """
    USNO predictions round to nearest minute so we use this hack to follow that.
    """
    return (dt + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0)


def night_header(year=2021):
    """
    Return header string for a night or set of nights
    """
    hdr = TBL_HDR.format(year)
    return hdr


def page_header(year=2021, create_time=datetime.datetime.now()):
    """
    Return header string for a page of almanac output
    """
    date = create_time.strftime("%B %d, %Y")
    with open(PAGE_HDR_FILE) as fp:
        hdr = fp.read().format(year, date)
    return hdr


def ascii_night(create_time=datetime.datetime.now()):
    """
    Takes a dict() as produced by nightly_almanac() and prints out string in a format that matches the MMTO's
    printed almanac.
    """
    create_time = Time(create_time)
    almanac = nightly_almanac(create_time)
    date_str = almanac['MST'].strftime("%b %d")

    tset_str = nearest_minute(almanac['Sunset'].to_datetime(timezone=TZ)).strftime(HM_STR)

    eve_str = ""
    for h in HORIZONS.keys():
        eve_str += nearest_minute(almanac[f"Eve {h}"].to_datetime(timezone=TZ)).strftime(HM_STR)
        eve_str += "   "

    ra3_west_str = "{:02d} {:02d}".format(int(almanac['RA 3 Hr West'].hms.h), int(almanac['RA 3 Hr West'].hms.m))

    midnight_st = almanac['Midnight ST'].to_string(unit=u.hourangle, sep=' ', precision=0)

    ra3_east_str = "{:02d} {:02d}".format(int(almanac['RA 3 Hr East'].hms.h), int(almanac['RA 3 Hr East'].hms.m))

    morn_str = ""
    keys = list(HORIZONS.keys())
    keys.reverse()
    for h in keys:
        morn_str += nearest_minute(almanac[f"Morn {h}"].to_datetime(timezone=TZ)).strftime(HM_STR)
        morn_str += "   "

    trise_str = nearest_minute(almanac['Sunrise'].to_datetime(timezone=TZ)).strftime(HM_STR).format("{:5s}")

    moon_rise = almanac['Moon Rise']
    moon_set = almanac['Moon Set']

    if moon_rise < almanac['Sunrise'] and moon_rise > almanac['Sunset']:
        mr_str = nearest_minute(moon_rise.to_datetime(timezone=TZ)).strftime(HM_STR)
    else:
        mr_str = "     "
    if moon_set > almanac['Sunset'] and moon_set < almanac['Sunrise']:
        ms_str = nearest_minute(moon_set.to_datetime(timezone=TZ)).strftime(HM_STR)
    else:
        ms_str = "     "

    moon_ill = "{:3d}".format(int(round(100 * almanac['Moon Illumination'])))

    age_str = "{:5.1f}".format(almanac['Moon Age'])

    outstr = "{:6s}    {:5s}   {:24s}{:5s}     {:8s}    {:5s}   {:24s}{:5s}     {:5s}   {:5s}   {:3s}     {:5s}\n".format(
        date_str,
        tset_str,
        eve_str,
        ra3_west_str,
        midnight_st,
        ra3_east_str,
        morn_str,
        trise_str,
        mr_str,
        ms_str,
        moon_ill,
        age_str
    )

    return outstr


def ascii_month(month=1, year=2021):
    """
    Generate a month of ascii almanac output following the traditional MMT almanac format
    """
    r = list(pd.date_range(start=f"{month}/1/{year}", end=f"{month+1}/1/{year}")[1:])

    outstr = night_header(year=year) + "\n"

    with Pool(processes=8) as pool:
        alines = pool.map(ascii_night, r)

    outstr += "".join(alines)

    return outstr
