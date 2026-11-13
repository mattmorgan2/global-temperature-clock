# Exploratory HEALPix land coverage

This analysis uses actual coordinates and the existing **1976–2025** daily
completeness metrics. It does not change first-pass eligibility, daily validity,
completeness calculations, or the website. Every day in that period has equal
weight. No country/continent assignments, quotas, extra stations for empty cells,
or historical/recent quality preferences enter the geographic calculations.
No final stations are selected.

## Inputs and dependencies

Run from the repository root with Python 3.12:

```sh
.venv/bin/python -m pip install -r analysis/healpix/requirements.lock.txt
.venv/bin/python -m unittest discover -s analysis/healpix -p 'test_*.py' -v
.venv/bin/python analysis/healpix/analyze.py
.venv/bin/python analysis/healpix/report.py
```

`requirements.txt` lists direct dependencies; `requirements.lock.txt` records the
installed versions including transitive dependencies. The editable project
package is not needed by the geographic analysis script.

The frozen input is
`data/processed/geography/inputs/completeness-1976-2025.csv` (5,243 candidate
station IDs). It is copied from the completed 50-year analysis, not recalculated
or filtered by recency. Candidates have TMAX and TMIN first years <=1976 and
last years >=2026. The input retains original metadata, country labels, daily
validity counts and paired-day percentages. Country fields are output labels
only. `source-provenance.json` accompanies the input. The frozen input and
provenance are versioned with the geographic results; the temporary driver and
raw daily downloads are excluded. Preserve this inputs folder with the analysis
outputs when sharing a reproducible run. The geographic
script independently checks its expected 18,263-day denominator and exact
threshold counts; it does not invoke the daily pipeline.

Input/output locations can be overridden with `--stations`, `--raw`, `--output`.
The default land cache is `data/raw/geography/`; outputs are
`data/processed/geography/healpix/`. Existing land datasets and fine sampling
arrays are reused. Daily NOAA downloads are not needed for this geographic run.

## Land source and geometry

The public-domain **Natural Earth 1:10m physical land and lakes datasets** are
used, pinned to the `nvkelso/natural-earth-vector` GitHub commit
`ca96624a56bd078437bca8184e78163e5039ad19`:

- `geojson/ne_10m_land.geojson`
- `geojson/ne_10m_lakes.geojson` (Lake, Reservoir, Alkaline Lake)

Exact raw URLs and SHA-256 hashes are in output provenance. Dataset information:
https://www.naturalearthdata.com/downloads/10m-physical-vectors/ . Natural Earth
terms: https://www.naturalearthdata.com/about/terms-of-use/ .

All lake/reservoir polygons are subtracted from land. Antarctica is included as
represented by Natural Earth's coastline. The dataset is a generalized present
land mask, not a historical shoreline reconstruction, and does not include every
microscopic island or waterbody. Station movement and coastline history are not
inferred.

HEALPix **NESTED** ordering uses NSIDE 1, 2, 4, 8: 12, 48, 192, 768 equal-area
cells over the sphere. Radius is the IUGG mean Earth radius, 6,371.0088 km.
Assignment uses `healpy.ang2pix` on station coordinates. Curved cell edges are
densified at 256 samples per side, unwrapped across the dateline and handled
explicitly at poles. Land polygons are intersected with those boundaries and
areas integrated on the sphere with `pyproj.Geod`. No coastal cell is assumed
entirely land. Any positive polygon-intersection area >1e-9 km² counts as land;
that tiny numerical tolerance is not a substantive minimum-land rule. Very small
land slivers are counted and flagged separately in coverage tables.

The script compares with 128 samples per side, checks theoretical equal cell
areas, and reconciles summed intersections with the entire land-minus-lakes
area. Numerical integration is approximate and convergence errors are recorded.

**Land in an occupied cell is a coverage proxy.** A station can occupy a large
cell while being thousands of kilometres from much of its land. It does not
mean all that land is observationally represented by the station. Point-mask
mismatches are flagged; all otherwise qualifying candidates remain included.

## Spacing and sampling

Distances are spherical great-circle kilometres. cKDTree nearest searches use
3D unit vectors; monotonic chord-to-angle conversion gives the great-circle
nearest station without dateline discontinuities.

For every grid/threshold configuration, the analysis records:

- All unordered station-pair distances where the two cell IDs differ, with
  distance quantiles and minimum/maximum.
- Each station's nearest candidate in another cell, with its distribution.
  These statistics are station-weighted; dense areas contribute more stations.
- All pairs of occupied neighboring cells, where neighbors share an edge **or
  vertex** (`healpy.get_all_neighbours`). Each row identifies the closest
  candidate pair, its separation and each point's distance to its own cell
  boundary (densified spherical arcs). Counts at 50/100/250 km are reported.
  A diagnostic boundary cluster means separation <=100 km and each point within
  50 km of its own boundary. The pair may be near a shared corner. These cutoffs
  are exploratory diagnostics, not eligibility or selection rules.

Land-nearest-station distributions use **all land-containing pixel centers** of
HEALPix NSIDE 1024: approximately equal-area samples at 40.54 km² per pixel.
Centers are tested against the land-minus-lakes polygons, including Antarctica.
Every accepted center has equal area weight; there are no country weights.
Results are compared with NSIDE 512 sampling and the sampled land-area estimate
is compared with polygon-integrated land area. A tiny island can have no sample
center even though its land is counted exactly in the coverage tables. These
are finite-resolution approximations, not exact continuous-land extrema.
The full sample pixel IDs are saved for reproducibility.

The all-candidate nearest-distance distribution is **independent of coarse grid
resolution**, and is an optimistic lower bound on any subset network.

To investigate one-per-cell spacing, 32 seeded diagnostic simulations choose
one candidate uniformly within each occupied land cell, using all occupied cells
and no additions for empty cells. Each simulation is measured against the same
100,000-point uniform subset of the fine land sample. Seed is 20261111, with
deterministic configuration offsets. Output contains summary distributions,
not proposed station lists. There is no claim these random networks are optimal
or that their station count is the correct final count. They measure sensitivity
to which candidate within a cell is chosen.

## Outputs

- `report.md`: interpretation, all 24 coverage rows, distance tables and recommendations.
- `coverage.csv`: totals, land/occupied/empty cells, represented land area,
  station-count distribution and singleton cells, coastal/point-mask flags.
- `cell-coverage.csv`: land fraction and candidate count for every cell/case.
- `station-cell-assignments.csv`: all input rows, four HEALPix IDs and six eligibility flags.
- `spacing.csv`, `neighbor-cell-pairs.csv`: cross-cell and boundary diagnostics.
- `land-nearest-station-distances.csv`: six all-candidate distance distributions.
- `one-per-cell-simulations.csv`, `one-per-cell-summary.csv`: seeded diagnostics.
- `land-distance-sample.npz`: sample HEALPix IDs and simulated-network sample indices.
- `maps/`: four PNG/PDF triptychs, each showing 70%, 85%, 95% (12 world-map panels).
  Green is land within an occupied cell, orange is unoccupied land, blue is
  ocean/inland water; black dots are all qualifying candidate stations.
- `validation.json`, `provenance.json`: geometry/sampling checks, hashes, sources,
  versions, parameters and code identity.

`--no-maps` skips rendering; `--simulations` and `--simulation-land-points`
control simulation cost. Keep the documented sampling and boundary resolutions
for the validated default analysis.
