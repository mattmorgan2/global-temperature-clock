# First-pass eligibility and pending methodology

NOAA GHCN-Daily is the observation source. The first-pass filter uses only
metadata, not daily observations. No final station-selection method or global
temperature calculation has been selected or implemented.

## Implemented metadata filter

Sources (NOAA fixed-width format):

- https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt
- https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt
- https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-countries.txt

Station fields use columns 1–11 (ID), 13–20 (latitude), 22–30 (longitude),
32–37 (elevation, metres), and 42–71 (name). Country code is the first two
characters of the station ID, joined to country columns 1–2 and name from
column 4 onward. These are NOAA codes, not assumed ISO country codes.
Inventory fields use columns 1–11 (ID), 32–35 (element), 37–40 (first year),
and 42–45 (last year). Coordinates come from station metadata, not inventory.

For target year Y, retain a station only if both inventory entries exist:

- TMAX first year <= 1926 and last year >= Y.
- TMIN first year <= 1926 and last year >= Y.

Y defaults dynamically to the current UTC calendar year; `--year` supports a
recorded historical replay. Unrelated elements do not affect eligibility.
Duplicate TMAX/TMIN inventory keys, duplicate station IDs, missing station joins,
and missing country names for qualifying stations fail visibly rather than
silently dropping or multiplying results. Elevation -999.9 means missing and
is exported as an empty field.

**An inventory range only identifies endpoint years with records.** A qualifying
station may have substantial gaps between those endpoints, including missing
days, months or years. The filter does not establish paired TMAX/TMIN observations
on the same days, current-year completeness, quality-flag acceptance, reporting
latency, or continuous operation. No daily data are downloaded or examined.
It makes no assumptions about station moves, instrumentation or homogenization.
It does not select the final 50 stations, balance geography, weight observations,
or establish a representative global sample.

Run commands and cache/output details are in the README. Cached bytes are checked
against locally recorded SHA-256 hashes (integrity/replay, not an independently
signed NOAA checksum). Preserve source snapshots for reproducibility because
live NOAA files change. A dirty Git revision in provenance requires preserving
the accompanying source diff as well; the commit ID alone cannot reproduce it.

## Decisions still pending

Before publishing estimates, explicitly decide and document:

- Station inclusion, geographic coverage, station history and eligibility rules.
- Measurement variables, units, quality flags and missing-data handling.
- Daily time boundaries, reporting delays and later revisions.
- Spatial weighting, aggregation, baseline (if used) and uncertainty reporting.
- Validation against independent references and limitations of coverage.

Reproducibility requirements for the future pipeline:

- Preserve source URLs, retrieval timestamps, source versions and SHA-256 hashes.
- Record the Git commit, Python version, dependency versions and all parameters.
- Keep raw inputs immutable; make each transformation explicit and testable.
- Publish a versioned output schema with units, provenance, coverage and limitations.
- Provide a documented command that recreates an output from recorded inputs.

The metadata workflow already records input hashes, retrieval metadata, parameters,
Python version, Git state and a CSV hash. Daily observation processing, scientific
validation and temperature calculations remain future work.

## Second-stage daily completeness

The input is the committed first-pass qualifying CSV. First-pass eligibility
rules are unchanged. This stage examines the station-specific files at
`https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/STATION_ID.dly`.

### Period, validity and threshold

The analysis window is fixed, inclusive **1926-01-01 through 2025-12-31**:
36,525 calendar days. Gregorian leap rules include 2000-02-29. Missing months,
missing temperature elements, and dates before/after a station's available
records within this window are incomplete, not removed from the denominator.
Nonexistent day slots (e.g. February 30) are excluded. Duplicate temperature
months, incorrect station IDs and malformed temperature records fail visibly.

Each `.dly` record uses station ID columns 1–11, year 12–15, month 16–17,
element 18–21, followed by 31 eight-character blocks: five-character integer
VALUE, MFLAG, QFLAG, SFLAG. Temperatures are tenths of degrees Celsius; no
conversion is needed to test presence. A valid element-day requires VALUE not
`-9999` and **QFLAG exactly blank**. A complete day requires both valid TMAX
and valid TMIN on the same GHCN calendar date.

Per NOAA's [format documentation](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt),
the nonblank quality flags excluded are:

| QFLAG | Meaning |
|---|---|
| D | Duplicate check failed |
| G | Gap check failed |
| I | Internal consistency check failed |
| K | Streak/frequent-value check failed |
| L | Multiday-period length check failed |
| M | Megaconsistency check failed |
| N | Naught check failed |
| O | Climatological outlier check failed |
| R | Lagged range check failed |
| S | Spatial consistency check failed |
| T | Temporal consistency check failed |
| W | Temperature too warm for snow |
| X | Bounds check failed |
| Z | Official Datzilla investigation flag |

Any unknown nonblank QFLAG is also excluded and reported. A blank QFLAG means
NOAA did not flag a quality-check failure; it is not an independent guarantee
that the observation is correct. MFLAG (measurement) and SFLAG (source) do not
exclude values here, including measurement flags H/L or source S. Flags occupy
separate fields and must not be confused. No extra plausibility checks (such as
TMIN <= TMAX), infilling, interpolation or homogenization are applied.

For each station, paired completeness = 100 × paired-valid days / 36,525.
Eligibility uses the exact integer comparison `paired_days * 100 >= 36525 * 95`,
not a rounded displayed percentage. At least **34,699** paired-valid days pass;
34,698 fail. All original metadata are carried into both output CSVs.
The longest incomplete run counts consecutive calendar days lacking either
valid element, including runs across month/year boundaries and at both ends
of the analysis period. QC rejection counts count nonmissing element-values
excluded for nonblank QFLAG; a day with two rejected elements contributes two
values to the aggregate QC-flag distribution.

### Interpretation and reproducibility

95% coverage can allow a multiyear gap. This stage measures coverage, not
strictly uninterrupted continuity. Annual/seasonal coverage, station moves,
observation-time changes, instrument history, geographic representativeness,
independence and suitability for global aggregation remain unassessed. Station
moves are deliberately ignored; no final approximately 50 stations are chosen.

Summary completeness bins are lower-inclusive/upper-exclusive except the final
99–100% bin, which includes 100%. The primary median covers **all first-pass
stations**; a separate median covers passers. Country counts refer to NOAA's
country/territory codes and are for the passing pool. Empty passing pools have
null passing median/minimum. The run records individual source hashes and
retrieval timestamps, input-list hash, output hashes, and code hashes. An
uncommitted implementation requires its matching code files as well as the
recorded Git base commit for exact reproduction. Cached checkpoints are invalidated
when the daily input, analysis code or period changes. Files absent from cache
are downloaded; cached files are reused unless explicitly refreshed.
