# Exploratory land-area facility location

This experiment fits **trial** GHCN-Daily station subsets, not a final network.
It reads [the decision log](../../docs/decisions.md) as constraints and reuses the
existing [HEALPix analysis](../healpix/README.md) data. It does not modify station
eligibility, daily completeness, the provisional missing-day rule or methodology.

## Reproduce

From the repository root, with Python 3.12 and the existing environment:

```sh
.venv/bin/python -m pip install -r analysis/facility_location/requirements.txt
.venv/bin/python -m unittest discover -s analysis/facility_location -p 'test_*.py' -v
.venv/bin/python analysis/facility_location/optimize.py
.venv/bin/python analysis/facility_location/validate.py
.venv/bin/python analysis/facility_location/report.py
```

Dependencies reuse the pinned HEALPix lockfile; no new package is required.
Default output is `data/processed/geography/facility-location/`. Raw/computational
cache files are under `data/raw/geography/facility-location/`; do not commit those.
`--output` and `--cache` can isolate a replay. `--no-maps` skips map rendering.
`--training-points` and `--max-swaps` change approximation settings and must be
recorded; the completed default experiment uses 16,384 training points per fit
and at most 32 improving swaps per network.

## Frozen inputs

- `data/processed/geography/inputs/completeness-1976-2025.csv`: 5,243 stations
  whose TMAX and TMIN both start by 1976 and extend into 2026.
- `data/processed/geography/healpix/land-distance-sample.npz`: all 3,588,564
  land-containing NSIDE 1024 HEALPix pixel centers, plus the prior 100,000-point
  simulation sample indices. The geographic objective uses these **locations**,
  not coarse cell memberships.
- Prior HEALPix full-candidate distance distributions and random one-per-cell
  simulations, for lower bounds and comparison.

The land sample covers Natural Earth 1:10m land minus lakes/reservoirs, including
Antarctica. Its equal-area quadrature gives every accepted point the same weight
(about 40.54 km²). It is the same finite-resolution land approximation as before:
very small islands can lack a sample center, and coastlines are generalized.
No country/continent, population, station-density or completeness weights enter
the objective. The 1976–2025 window is inherited from the requested experiment;
all its days were equally weighted by the unchanged completeness calculation.

Eligibility thresholds are **70%, 80%, 85%, 95%** paired-valid days, evaluated by
exact integer comparisons with 18,263 calendar days. Completeness determines only
pool membership. It does not score, rank or break geographic ties. Trial network
sizes are **30, 50, 75, 100**, regardless of the number of occupied grid cells.

## Geographic objective and search

The discrete spherical p-median objective is the arithmetic mean of each land
sample location's great-circle distance to its nearest selected station. Earth
radius is 6,371.0088 km, matching the previous analysis. Distances, not squared
distances, are minimized. Median and tail distances are evaluated separately;
the algorithm does not minimize them or station-to-station distances.

A full 3,992 × 3,588,564 float32 distance matrix would require about 57 GB before
search work. To keep iterative fitting practical:

1. Draw two uniform, without-replacement subsets of **16,384 land sample points**
   with seeds **2026111301** and **2026111302**. Use the same subsets across all
   thresholds and network sizes. Persist their indices. No regional sampling
   weights or boundaries are introduced.
2. For each threshold and training subset, build a facility-by-demand distance
   matrix (float32 km, float64 objective reductions). Candidates are sorted by
   station ID solely for deterministic tie resolution. Storage precision can
   create effectively exact ties at approximately metre scale; completeness is
   never consulted. The largest stored distance matrix is about 250 MiB.
3. Greedily add the candidate giving the smallest resulting mean distance until
   100 facilities are present. The 30/50/75/100 prefixes initialize separate fits.
4. Refine each prefix with best-improving **one-for-one swaps**. Each pass evaluates
   all unselected additions and all possible removals using a FastPAM-style
   nearest/second-nearest assignment correction. Stop when no swap improves the
   training mean by more than **0.0001 km**, or after **32 accepted swaps**.
   A capped fit is explicitly marked nonconverged; a converged fit is only
   one-swap optimal on its training approximation, not globally optimal.
5. Score each of the two fitted networks against **all 3,588,564 land locations**
   and retain the fit with the smaller full-sample mean. This is the final
   objective evaluation, not a recent-completeness or climate-quality ranking.

The search uses no coarse HEALPix IDs, political boundaries, station quotas or
minimum-separation constraints. More candidates in a dense region provide more
feasible locations, but do not give that region extra demand weight. Mean-distance
optimization can still spend additional stations in already sampled regions when
no candidates are available in large gaps. This does not repair the gaps or imply
that the resulting network is uniformly spaced or climatically representative.

The two-fit design is a sensitivity check, not a global optimization guarantee.
Both fits' full-sample metrics, swap counts, remaining training improvement and
runtime are saved. Full-sample evaluation does not eliminate training/search
approximation error. The lowest mean among two heuristic solutions need not have
the lowest p95 or greatest station separation.

## Outputs and interpretation

- `comparison.csv`: all 16 retained trials, mean/median/p90/p95 and other land
  distance statistics, nearest-other-selected-station statistics, lower bounds,
  approximation status and incremental mean improvements.
- `networks/network-THRESHOLDpct-SIZE.csv`: all selected station IDs, names,
  coordinates, completeness metrics, order and fit identity. `is_final_network`
  is false. `selection_order` is the chronological order of **retained** members;
  `entered_at_algorithm_step` preserves greedy/swap-entry timing, including gaps
  for members later removed. It is not a station quality or importance ranking.
- `selection-trace.csv`: complete greedy prefixes and every accepted swap for
  both fits, grouped by threshold/restart/network size. Greedy prefix rows have
  network size zero because each prefix is shared across the four initializations.
- `restart-results.csv`: both fitted solutions for each configuration, allowing
  mean-distance sensitivity and convergence to be reviewed.
- `healpix-comparison.csv`: comparisons at the **same threshold** where prior
  random one-per-cell network size differs by at most 20% from the requested size.
  Compare distances on the **same prior 100,000 land sample points**. Sizes are
  explicitly shown and are not falsely presented as exactly matched. Absence of
  a baseline row means no reasonably size-comparable prior simulation existed.
- `coverage-improvement.png/.pdf`: mean and p95 versus network size, with
  full-candidate mean lower bounds (not achievable-optimum claims for fixed size).
- `maps/networks-THRESHOLDpct.png/.pdf`: four panels per threshold, one for each
  requested size (16 maps total). Triangles are trial stations; land color is
  nearest-station distance with a common 0–9,000 km scale. Ocean/lakes are blue.
- `optimization-demand-samples.npz`, `performance.csv`, `validation.json`, and
  `provenance.json`: sample identities, execution evidence, hashes, seeds and
  source/parameter/version records.
- `map-validation.json`: independent station marker counts for all 16 panels.
- `independent-validation.json`: full-land rescoring and deterministic 30-station replays.
- `report.md`: all comparisons, incremental gains and limitations; no final
  threshold, size or network recommendation is adopted.

Large per-land-point distance vectors used for rendering are cache files, not
source results. They can be regenerated from the selected network CSVs and the
versioned land sample. This experiment applies no missing-day fill and makes no
claims that geographic proximity establishes climatic representativeness.
