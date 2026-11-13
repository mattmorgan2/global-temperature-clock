# Inspection of the saved 70% / 50-station network

This read-only inspection uses the committed network CSV, frozen 1976–2025
completeness metrics, and its original cached GHCN `.dly` snapshots. It does not
select stations, optimize geography, apply infilling or change methodology.

From the repository root, using the existing HEALPix dependencies:

```sh
.venv/bin/python -m unittest discover -s analysis/network_review -p 'test_*.py' -v
.venv/bin/python analysis/network_review/review.py
.venv/bin/python analysis/network_review/validate.py
```

Dependencies are already pinned in `analysis/healpix/requirements.lock.txt`.
Results are saved under `data/processed/geography/network-review/`. CLI options
allow overriding the frozen inputs, daily cache and output paths. The original
canonical cache files must be retained under their content-addressed names;
missing files or mismatched hashes fail visibly rather than trigger a live
NOAA download or silently inspect newer observations.

The report and `station-review.csv` contain all 50 stations sorted by exact
historical paired-valid completeness, with a stable review number for the map.
They retain the original selection order and add gap dates, observed/QC-valid
year endpoints, inventory endpoints, elevation, and nearby candidate counts and
maxima at 50/100/250 km. Daily validity uses the existing definition: nonmissing
TMAX and TMIN, both with blank QFLAG. Measurement/source flags do not independently
invalidate values. All period days count equally; missing months/elements remain
in the denominator. No recent/historical preference is applied.

Primary nearby statistics use the 3,992 candidates eligible at 70%, excluding
self. Secondary columns use all 5,243 pre-threshold candidates. Other selected
IDs are not arbitrarily excluded, although this network's >916 km minimum
separation means none fall within the requested radii. Distances are spherical
great-circle km with the same 6,371.0088-km Earth radius as the original analysis.

The descriptive “substantially more complete” flag is a >=5-percentage-point
historical completeness gain within 100 km, checked using exact day counts.
This is an inspection convention, not a new eligibility rule or a replacement
proposal. The flagged-station table displays the highest completeness (ties by
nearer distance, then ID); the full pair CSV retains every observation meeting
the flag. Geographic replacement effects, climatic equivalence, station moves,
and suitability of neighboring sites are not assessed.

Longest gaps use inclusive dates restricted to 1976–2025. Ties are all retained
in `longest-gaps.csv`; the main table shows the earliest tied interval. All gap
runs are retained in `incomplete-runs.csv`. Observed year endpoints cover the
entire cached daily file and include any nonmissing value, even QC-flagged;
QC-valid endpoints and original inventory endpoints are separate columns.
None of those endpoints establishes continuous coverage.

`validate.py` independently reconstructs paired date sets/gap intervals, checks
neighbor counts and maxima using haversine distances, validates source/output
hashes, and confirms the copied original coverage-statistics row and unchanged
selected-station input. It writes `validation.json` and finalizes the report
bundle manifest in `provenance.json`. Tests cover leap days, tied gaps, QC flags,
absent elements, complete days, observed versus valid endpoints, self exclusion,
radius boundaries, empty neighborhoods and exact completeness-gain boundaries.

## Provisional missing-data rule (not applied here)

The [decision log](../../docs/decisions.md#provisional-same-calendar-date-substitution)
is the canonical definition: for a missing station observation, the provisional
substitute is the arithmetic mean of its ten most recent valid observations for
**the same month and day in preceding years**, skipping years without valid
measurements. A valid daily observation requires both TMAX and TMIN to be present
and have blank quality flags. Do not use the preceding ten calendar days,
previously substituted values, or future years. The fallback with fewer than ten
valid same-date observations and February 29 handling remain open questions.
This inspection applies no substitution and does not implement that provisional
rule.

The saved provenance retains the original numerical inspection-run script hash.
Its `documentation_update` entry records the corrected report-generator hash;
only report wording changed, with numeric outputs and maps preserved. The
validation command rechecks the original network and results without optimization.
