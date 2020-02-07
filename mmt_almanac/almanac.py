# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

import datetime
import pytz

from functools import partial
import multiprocessing as mp

import pandas as pd

import astroplan

import astropy.units as u

from astropy.coordinates import EarthLocation
from astropy.time import Time

from skyfield import api
from skyfield import almanac

SKYFIELD_TS = api.load.timescale()
SKYFIELD_EPHEM = api.load('de421.bsp')
TZ = pytz.timezone("America/Phoenix")

# This value bakes in an assumed average amount of atmospheric refraction. Use for consistency with USNO rise/set calculations.
USNO_HORIZON = -(5/6) * u.deg

HORIZONS = {
    "6 Deg": -6 * u.deg,
    "12 Deg": -12 * u.deg,
    "18 Deg": -18 * u.deg
}

MMT_LOCATION = EarthLocation.from_geodetic("-110:53:04.4", "31:41:19.6", 2600 * u.m)
MMT = astroplan.Observer(name="MMTO", location=MMT_LOCATION, timezone="US/Arizona", pressure=0*u.mbar)


def calc_newmoons(time=Time.now(), nmonths=2):
    """
    Use skyfield to calculate an array of new moon times that will be used to calculate moon age in days.
    """
    begin = (time - nmonths/12 * u.year).to_datetime()
    end = (time + nmonths/12 * u.year).to_datetime()
    t0 = SKYFIELD_TS.utc(begin.year, begin.month, begin.day)
    t1 = SKYFIELD_TS.utc(end.year, end.month, end.day)
    phase_times, phase_flags = almanac.find_discrete(t0, t1, almanac.moon_phases(SKYFIELD_EPHEM))
    newmoons = phase_times[phase_flags == 0]
    return newmoons


def nightly_almanac(time=Time.now(), newmoons=None, n_grid_points=150):
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
        newmoons = calc_newmoons(time, nmonths=2)

    alm_dict['UT'] = time
    alm_dict['MST'] = local_t
    alm_dict['Sunset'] = MMT.sun_set_time(night_start, which='next', horizon=USNO_HORIZON, n_grid_points=n_grid_points)
    for k, h in HORIZONS.items():
        alm_dict["Eve " + k] = MMT.sun_set_time(night_start, which='next', horizon=h, n_grid_points=n_grid_points)

    alm_dict['RA 3 Hr West'] = alm_dict['Eve 18 Deg'].sidereal_time(kind='apparent', longitude=MMT.location.lon)
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'] - 3 * u.hourangle
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'].wrap_at(24 * u.hourangle)

    # set up local midnight for the date we're calculating
    midnight = Time(f"{str(local_t.date())} 07:00:00") + 1 * u.day
    alm_dict['Midnight ST'] = midnight.sidereal_time(kind='apparent', longitude=MMT.location.lon)

    alm_dict['Sunrise'] = MMT.sun_rise_time(night_start, which='next', horizon=USNO_HORIZON, n_grid_points=n_grid_points)
    for k, h in HORIZONS.items():
        alm_dict["Morn " + k] = MMT.sun_rise_time(night_start, which='next', horizon=h, n_grid_points=n_grid_points)

    alm_dict['RA 3 Hr East'] = alm_dict['Morn 18 Deg'].sidereal_time(kind='apparent', longitude=MMT.location.lon)
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'] + 3 * u.hourangle
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'].wrap_at(24 * u.hourangle)

    alm_dict['Moon Rise'] = MMT.moon_rise_time(night_start, which='next', horizon=USNO_HORIZON, n_grid_points=n_grid_points)
    alm_dict['Moon Set'] = MMT.moon_set_time(night_start, which='next', horizon=USNO_HORIZON, n_grid_points=n_grid_points)

    alm_dict['Moon Illumination'] = MMT.moon_illumination(midnight)

    newmoon_diff = midnight.to_datetime(timezone=pytz.utc) - newmoons.utc_datetime()
    nearest = abs(newmoon_diff).argmin()
    alm_dict['Moon Age'] = newmoon_diff[nearest].total_seconds()/86400
    night_length = alm_dict['Morn 12 Deg'].to_datetime() - alm_dict['Eve 12 Deg'].to_datetime()
    alm_dict['Night Length'] = night_length.total_seconds()/3600

    return alm_dict


def monthly_almanac(time=Time.now(), newmoons=None, n_grid_points=150):
    """
    Generate MMTO almanac information for a given month. By default do the current month.
    """
    time = Time(time)
    local_t = time.to_datetime(timezone=TZ)
    m = local_t.month
    y = local_t.year
    ndays = pd.Period(local_t.strftime('%b %y')).days_in_month

    # if set of new moon dates not provided, calculate the set that fully brackets the given time.
    if newmoons is None:
        newmoons = calc_newmoons(time, nmonths=3)

    date_range = pd.date_range(start=f"{m}/1/{y}", periods=ndays)
    ncores = mp.cpu_count()
    pool = mp.Pool(processes=ncores)
    try:
        alms = pool.map(partial(nightly_almanac, newmoons=newmoons, n_grid_points=n_grid_points), date_range)
    finally:
        pool.close()
        pool.join()

    return alms


def yearly_almanac(year=2020, newmoons=None, n_grid_points=150):
    """
    Generate MMTO almanac information for a given year.
    """
    months = [datetime.date(year, m, 1).strftime("%b") for m in range(1, 13)]

    if newmoons is None:
        newmoons = calc_newmoons(Time(f"{year}-6-15"), nmonths=8)  # this is a little hacky, but whatever.

    alm_dict = {}
    for m in range(0, 12):
        alm_dict[months[m]] = monthly_almanac(time=f"{year}-{m+1}-15", newmoons=newmoons, n_grid_points=n_grid_points)

    return alm_dict
