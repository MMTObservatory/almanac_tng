# Licensed under a 3-clause BSD style license - see LICENSE.rst
# coding=utf-8

import json

from .almanac import nightly_almanac, TZ
from .ascii import HM_STR

DB_TIMES_MAP = {
    "sunrise_next": "Sunrise",
    "sunset_previous": "Sunset",
    "moonrise_next": "Moon Rise",
    "moonset_previous": "Moon Set",
    "begin_civil_twilight": "Morn 6 Deg",
    "begin_nautical_twilight": "Morn 12 Deg",
    "begin_astronomical_twilight": "Morn 18 Deg",
    "end_civil_twilight": "Eve 6 Deg",
    "end_nautical_twilight": "Eve 12 Deg",
    "end_astronomical_twilight": "Eve 18 Deg"
}


MISC_KEY_MAP = {
    "length_night": "Night Length",
    "moon_age": "Moon Age",
    "moon_illum": "Moon Illumination"
}


def json_night(almanac=nightly_almanac(), pretty=False):
    """
    Takes a dict() as produced by nightly_almanac() and creates JSON output that
    """
    jdict = {}
    now = almanac['MST']  # old code uses datetime.now() which defaults to local time
    jdict['date'] = now.strftime('%Y-%m-%d')
    jdict['timestamp'] = now.strftime("%s")

    # the original script assumes it is run at night. this code checks the sun and moon elevation
    # and if they're up, use next set time, but if they're down, use previous. keep the keys the
    # same here, though, for API compatibility elsewhere.
    for k, i in DB_TIMES_MAP.items():
        jdict[k] = almanac[i].to_datetime(timezone=TZ).strftime(HM_STR)
        jdict[k + "_timestamp"] = almanac[i].to_datetime(timezone=TZ).strftime("%s")

    for k, i in MISC_KEY_MAP.items():
        jdict[k] = almanac[i]

    if pretty:
        almanac_json = json.dumps(jdict, sort_keys=True, indent=4)
    else:
        almanac_json = json.dumps(jdict, separators=(',', ':'))
    return almanac_json
