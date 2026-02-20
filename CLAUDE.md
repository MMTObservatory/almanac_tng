# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`almanac_tng` is the MMT Observatory's almanac software — tools to generate the MMT telescope's yearly almanac and nightly schedules. It uses `astropy`, `astroplan`, and `skyfield` for astronomical calculations, and outputs both ASCII (traditional printed format) and JSON formats.

The package is `mmt_almanac` (importable name), versioned via `setuptools_scm` from git tags.

## Common Commands

### Running Tests
```bash
# Run all tests (preferred: uses tox environments)
tox -e py314-alldeps

# Run tests directly with pytest (faster for development)
pytest --pyargs mmt_almanac

# Run a single test file
pytest mmt_almanac/tests/test_daily.py

# Run tests with coverage
tox -e py314-alldeps-cov

# Run doctest on RST docs too (as tox does)
pytest --pyargs mmt_almanac docs/
```

### Code Style
```bash
tox -e codestyle
# or directly:
flake8 mmt_almanac --count --max-line-length=127
```

### Build Docs
```bash
tox -e build_docs
# or directly from docs/:
sphinx-build -W -b html docs/ docs/_build/html
```

### CLI Entry Points
```bash
update_iers_a          # Download latest IERS-A Earth orientation data (needed before generating almanac)
yearly_almanac -y 2025 -o almanac.txt   # Generate full year ASCII almanac
```

## Architecture

### Core Computation (`almanac.py`)
All astronomical calculations live here. Key objects:
- `MMT_LOCATION` / `MMT` — site location (Mt. Hopkins, AZ) as `EarthLocation` and `astroplan.Observer`
- `SKYFIELD_EPHEM` / `SKYFIELD_TS` — skyfield ephemeris (de421.bsp) loaded at module import
- `TZ` — `pytz` timezone for America/Phoenix (no DST)
- `USNO_HORIZON` — `-5/6 deg` horizon matching USNO rise/set convention (atmospheric refraction)
- `HORIZONS` dict — civil/nautical/astronomical twilight depths (6/12/18 deg)

Computation hierarchy:
- `nightly_almanac(time)` → dict of `astropy.time.Time` objects for one night
- `monthly_almanac(time)` → list of nightly dicts, parallelized with `multiprocessing.Pool`
- `yearly_almanac(year)` → dict keyed by month name containing lists of nightly dicts

### Output Modules
- `ascii.py` — formats nightly dicts into the traditional MMTO fixed-width ASCII almanac format; `yearly_almanac()` is the CLI entry point
- `json.py` — formats nightly dicts into JSON for the observatory database/API

### Testing Notes
- Tests use reduced `n_grid_points` (e.g., 5–12 instead of 150) to speed up calculations
- `pytest-astropy` provides doctest support for RST files (`--doctest-rst` is set in `pyproject.toml`)
- `update_iers_a` is run as part of the tox test commands to ensure current Earth orientation data

### Data Files
- `de421.bsp` — JPL ephemeris file (gitignored, downloaded by skyfield at runtime)
- `header.txt` — ASCII template for the printed almanac page header
- `Leap_Second.dat`, `deltat.*` — skyfield data files (gitignored, downloaded at runtime)

### PDF Generation
Tagged releases (e.g., `v2025.0.0`) trigger a GitHub Actions workflow that generates the PDF almanac. The major version component is used as the almanac year.
