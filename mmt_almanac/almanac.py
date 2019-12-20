import pkg_resources
import datetime
import time
import os
import sys
import pytz
from pathlib import Path

import numpy as np
import pandas as pd

import astroplan
import skyfield

import astropy.units as u

from astropy.coordinates import EarthLocation
from astropy.time import Time

from skyfield import api
from skyfield import almanac

SKYFIELD_TS = api.load.timescale()
SKYFIELD_EPHEM = api.load('de421.bsp')
TZ = pytz.timezone("America/Phoenix")

# This value bakes in an assumed average amount of atmospheric refraction. Use for consistency with USNO rise/set calculations
USNO_HORIZON = -(5/6) * u.deg

HORIZONS = {
    "6 Deg": -6 * u.deg,
    "12 Deg": -12 * u.deg,
    "18 Deg": -18 * u.deg
}

MMT_LOCATION = EarthLocation.from_geodetic("-110:53:04.4", "31:41:19.6", 2600 * u.m)
MMT = astroplan.Observer(name="MMTO", location=MMT_LOCATION, timezone="US/Arizona", pressure=0*u.mbar)

TBL_HDR = f"     {year}          Sun     Sun     Sun    RA 3H                RA 3H    Sun     Sun     Sun               Moon    Moon   Moon @ Midnight\n"  # noqa
TBL_HDR += " Date    Sunset   6 Deg   12 Deg  18 Deg  West at  Sid Time    East at 18 Deg  12 Deg  6 Deg  Sunrise     rise    set    Illum     Age  \n"  # noqa
TBL_HDR += "                  W Hrz   W Hrz   W Hrz   18 Deg   Midnight    18 Deg  E Hrz   E Hrz   E Hrz                               %       Days\n"  # noqa


def nearest_minute(dt):
    """
    USNO predictions round to nearest minute so we use this hack to follow that.
    """
    return (dt + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0)


def hm_string(dt):
    """
    The traditional MMTO almanac format displays time as "HH MM" with no leading zero on the hour.
    """
    hm_str = nearest_minute(dt).strftime("%-H %M")
    return hm_str


def nightly_almanac(time=Time.now(), newmoons=None):
    """
    Generate MMTO almanac information for a given time. The given time or date is assumed to be in MST.
    """
    time = Time(time)
    local_t = time.to_datetime(timezone=TZ)

    # almanac day is MST, but its night falls into the next day in UT
    night_start = Time(f"{str(local_t.date())} 00:00:00") + 1 * u.day

    alm_dict = {}
    # if set of new moon dates not provided, calculate the set that fully brackets the given time.
    if newmoons is None:
        begin = (time - 2 * u.month).to_datetime()
        end = (time + 2 * u.month).to_datetime()
        t0 = SKYFIELD_TS.utc(begin.year, begin.month, begin.day)
        t1 = SKYFIELD_TS.utc(end.year, end.month, end.day)
        phase_times, phase_flags = almanac.find_discrete(t0, t1, almanac.moon_phases(SKYFIELD_EPHEM))
        newmoons = phase_times[phase_flags == 0]

    alm_dict['Sunset'] = MMT.sun_set_time(night_start, which='next', horizon=USNO_HORIZON)
    for k, h in HORIZONS.items():
        alm_dict["Eve " + k] = MMT.sun_set_time(night_start, which='next', horizon=h)

    alm_dict['RA 3 Hr West'] = alm_dict['Eve 18 Deg'].sidereal_time(kind='apparent', longitude=MMT.location.lon)
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'] - 3 * u.hourangle
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'].wrap_at(24 * u.hourangle)

    # set up local midnight for the date we're calculating
    midnight = Time(f"{str(local_t.date())} 07:00:00") + 1 * u.day
    alm_dict['Midnight ST'] = midnight.sidereal_time(kind='apparent', longitude=MMT.location.lon)

    alm_dict['Sunrise'] = MMT.sun_rise_time(night_start, which='next', horizon=usno_horizon)
    for k, h in HORIZONS.items():
        alm_dict["Morn " + k] = MMT.sun_rise_time(night_start, which='next', horizon=h)

    alm_dict['RA 3 Hr East'] = alm_dict['Morn 18 Deg'].sidereal_time(kind='apparent', longitude=mmt.location.lon)
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'] + 3 * u.hourangle
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'].wrap_at(24 * u.hourangle)

    alm_dict['Moon Rise'] = MMT.moon_rise_time(night_start, which='next', horizon=usno_horizon)
    alm_dict['Moon Set'] = MMT.moon_set_time(night_start, which='next', horizon=usno_horizon)
    alm_dict['Moon Illumination'] = MMT.moon_illumination(midnight)

    newmoon_diff = midnight.to_datetime(timezone=pytz.utc) - newmoons.utc_datetime()
    nearest = abs(newmoon_diff).argmin()
    alm_dict['Moon Age'] = newmoon_diff[nearest].total_seconds()/86400

    return alm_dict
