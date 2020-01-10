import pkg_resources
import datetime
import pytz

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

HM_STR = "%-H %M"
MMT_LOCATION = EarthLocation.from_geodetic("-110:53:04.4", "31:41:19.6", 2600 * u.m)
MMT = astroplan.Observer(name="MMTO", location=MMT_LOCATION, timezone="US/Arizona", pressure=0*u.mbar)

TBL_HDR = "     {:4d}          Sun     Sun     Sun    RA 3H                RA 3H    Sun     Sun     Sun               Moon    Moon   Moon at Midnight\n"  # noqa
TBL_HDR += " Date    Sunset   6 Deg   12 Deg  18 Deg  West at  Sid Time    East at 18 Deg  12 Deg  6 Deg  Sunrise     rise    set    Illum     Age  \n"  # noqa
TBL_HDR += "                  W Hrz   W Hrz   W Hrz   18 Deg   Midnight    18 Deg  E Hrz   E Hrz   E Hrz                               %       Days\n"  # noqa

PAGE_HDR_FILE = pkg_resources.resource_filename(__name__, "header.txt")


def nearest_minute(dt):
    """
    USNO predictions round to nearest minute so we use this hack to follow that.
    """
    return (dt + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0)


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
        newmoons = calc_newmoons(time, nmonths=2)

    alm_dict['UT'] = time
    alm_dict['MST'] = local_t
    alm_dict['Sunset'] = MMT.sun_set_time(night_start, which='next', horizon=USNO_HORIZON)
    for k, h in HORIZONS.items():
        alm_dict["Eve " + k] = MMT.sun_set_time(night_start, which='next', horizon=h)

    alm_dict['RA 3 Hr West'] = alm_dict['Eve 18 Deg'].sidereal_time(kind='apparent', longitude=MMT.location.lon)
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'] - 3 * u.hourangle
    alm_dict['RA 3 Hr West'] = alm_dict['RA 3 Hr West'].wrap_at(24 * u.hourangle)

    # set up local midnight for the date we're calculating
    midnight = Time(f"{str(local_t.date())} 07:00:00") + 1 * u.day
    alm_dict['Midnight ST'] = midnight.sidereal_time(kind='apparent', longitude=MMT.location.lon)

    alm_dict['Sunrise'] = MMT.sun_rise_time(night_start, which='next', horizon=USNO_HORIZON)
    for k, h in HORIZONS.items():
        alm_dict["Morn " + k] = MMT.sun_rise_time(night_start, which='next', horizon=h)

    alm_dict['RA 3 Hr East'] = alm_dict['Morn 18 Deg'].sidereal_time(kind='apparent', longitude=MMT.location.lon)
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'] + 3 * u.hourangle
    alm_dict['RA 3 Hr East'] = alm_dict['RA 3 Hr East'].wrap_at(24 * u.hourangle)

    alm_dict['Moon Rise'] = MMT.moon_rise_time(night_start, which='next', horizon=USNO_HORIZON)
    alm_dict['Moon Set'] = MMT.moon_set_time(night_start, which='next', horizon=USNO_HORIZON)
    alm_dict['Moon Illumination'] = MMT.moon_illumination(midnight)

    newmoon_diff = midnight.to_datetime(timezone=pytz.utc) - newmoons.utc_datetime()
    nearest = abs(newmoon_diff).argmin()
    alm_dict['Moon Age'] = newmoon_diff[nearest].total_seconds()/86400
    night_length = alm_dict['Morn 12 Deg'].to_datetime() - alm_dict['Eve 12 Deg'].to_datetime()
    alm_dict['Night Length'] = night_length.total_seconds()/3600

    return alm_dict


def ascii_night(almanac=nightly_almanac()):
    """
    Takes a dict() as produced by nightly_almanac() and prints out string in a format that matches the MMTO's
    printed almanac.
    """
    date_str = almanac['MST'].strftime("%b %d")

    tset_str = nearest_minute(almanac['Sunset'].to_datetime(timezone=TZ)).strftime(HM_STR)

    eve_str = ""
    for h in HORIZONS.keys():
        eve_str += nearest_minute(almanac[f"Eve {h}"].to_datetime(timezone=TZ)).strftime(HM_STR)
        eve_str += "   "

    ra3_west_str = "{:02d} {:02d}".format(int(almanac['RA 3 Hr West'].hms.h), int(almanac['RA 3 Hr West'].hms.m))

    midnight_st = almanac['Midnight ST'].to_string(sep=' ', precision=0)

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

    outstr = "{:6s}    {:5s}   {:24s}{:5s}     {:8s}    {:5s}   {:24s}{:5s}     {:5s}   {:5s}   {:3s}     {:5s}".format(
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


def monthly_almanac(time=Time.now(), newmoons=None):
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
    alm_dict = {}
    date_range = pd.date_range(start=f"{m}/1/{y}", periods=ndays)
    for d in date_range:
        night_alm = nightly_almanac(time=d, newmoons=newmoons)
        alm_dict[night_alm['Date']] = night_alm

    return alm_dict


def yearly_almanac(year=2020, newmoons=None):
    """
    Generate MMTO almanac information for a given year.
    """
    months = [datetime.date(year, m, 1).strftime("%b") for m in range(1, 13)]

    if newmoons is None:
        newmoons = calc_newmoons(Time(f"{year}-6-15"), nmonths=8)  # this is a little hacky, but whatever.

    alm_dict = {}
    for m in range(0, 12):
        alm_dict[months[m]] = monthly_almanac(time=f"{year}-{m+1}-15", newmoons=newmoons)

    return alm_dict
