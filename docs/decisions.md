# Global Daily Temperature Clock decision log

Recorded: **2026-11-13**. Experiment results below describe the saved November
2026 datasets; they are not promises about future NOAA updates.

This log separates project intent from implemented calculations and experimental
findings. Established principles and the provisional missing-day rule record the
project owner's instructions. Technical details and results are linked to their
repository sources. This document does not change the running methodology.

## Established project principles

- **Use actual recorded station temperatures.** Do not substitute modeled or
  homogenized global-temperature estimates for station observations. Retain
  source provenance and quality flags; using GHCN does not establish that every
  source stream has identical measurement or reporting characteristics.
- **Select by geography, not political boundaries.** Use actual station
  coordinates. Country and continent tables are descriptive diagnostics, not
  quotas or selection constraints.
- **Aim for roughly equal geographic representation of Earth's land areas.**
  Ocean portions of coastal cells must not be counted as land. Do not compensate
  for empty regions by adding extra stations in already well-covered areas.
- **Keep the station set fixed when calculating daily averages.** Missing data
  must not silently turn the daily calculation into an average of a changing
  available-station set. The final aggregation and missing-data implementation
  are not yet established.
- **Use both valid TMAX and TMIN.** In the existing GHCN completeness calculations,
  an observed complete day requires both values to be nonmissing and have blank
  quality flags. All nonblank quality flags are excluded, including unknown
  ones; measurement and source flags alone do not exclude a value. See the
  [implemented validity definition and flag list](methodology.md#period-validity-and-threshold).
- **Do not presume that recent completeness matters more than historical
  completeness.** No preference or temporal weighting has been adopted. The
  saved experiments weight every day in their specified window equally.
- **Keep calculations transparent and reproducible.** GitHub is the source of
  truth for code and reviewed artifacts. Preserve source identities, hashes,
  parameters and code versions. Keep Python data processing separate from the
  Astro website. See the [architecture](../README.md#architecture) and
  [methodology](methodology.md).

## Provisional decisions and working arrangements

| Item | Current provisional position | Limits / implementation status |
|---|---|---|
| Missing-day rule | For a missing observation, use the arithmetic mean of the same station’s **ten most recent valid observations for the same month and day in preceding years**. | Explicitly provisional and not implemented. Skip years without valid same-date observations; never use substituted values or future years. Fewer-than-ten fallback and February 29 handling remain open. See the precise definition below. |
| Observation source | GHCN-Daily is the source used by the existing pipeline and experiments. | This is not a decision that GHCN alone provides adequate worldwide coverage or that other observational sources are excluded. |
| Geographic exploration | HEALPix is the current equal-area grid tool for experiments. | No final grid resolution, grid orientation, one-station-per-cell rule, or optimization method has been adopted. Random one-per-cell simulations were diagnostics only. |
| Station history | Completed experiments have not assessed station moves. | This is not an assumption of location stability or a final policy on station-history treatment. |

### Provisional same-calendar-date substitution

For a missing station observation on month/day in year Y:

1. Look only at recorded observations from **the same station, for the same
   month and day, in years strictly preceding Y**.
2. A valid daily observation requires **both TMAX and TMIN to be present and
   have blank quality flags**. Skip years without a valid same-date observation.
3. Select the **ten most recent valid** observations meeting those conditions,
   then take their **arithmetic mean**. The ten observations need not come from
   ten consecutive years.
4. **Do not average the preceding ten calendar days. Do not use previously
   substituted values. Do not use observations from future years.**

For example, if **January 11, 2026** is missing, use the ten most recent valid
**January 11** observations from years **before 2026**, skipping years with
missing or invalid measurements. January 1–10, 2026 are not the input dates.

If fewer than ten prior valid same-date observations are available, the
**fallback is not yet decided**. **February 29 handling remains an open
question**; no mapping to another date or leap-day fallback has been adopted.

This rule remains **provisional and unimplemented**. It does not settle the
station daily-temperature formula or other open aggregation decisions. Its
same-date historical lookback does not introduce recent-completeness weighting
into station eligibility or geographic selection.

The provisional missing-day rule was **not** used to calculate eligibility,
paired-day completeness, or any saved HEALPix result. Those experiments count
only recorded, QC-valid TMAX/TMIN pairs. An estimated value must not be described
as an actual observed complete day in interpreting those results.

The first-pass 1926 cutoff, experimental 1976 cutoff and 95% passing pools are
implemented or tested settings, **not final scientific acceptance decisions**.
No final station set, station daily-temperature formula, or global daily-average
calculation has been selected or implemented.

## Open questions

| Question | What remains undecided |
|---|---|
| Historical window | **50, 70 or 100 years**. The completed comparisons use 1976–2025 and 1926–2025; the 70-year option has not been tested in these experiments. |
| Minimum completeness | No threshold is selected. Experiments compare 70%, 75%, 80%, 85%, 90% and 95%; overall percentages must be considered alongside gap lengths and timing. |
| Final station count | No number is fixed. Roughly 50 was an exploratory idea, not a requirement; occupied-cell counts do not determine the correct final number. |
| Geographic optimization | Final grid, resolution/orientation, within-cell choice, cross-boundary spacing, geographic objective and land/island treatment remain open. HEALPix occupancy alone does not establish even representation. |
| Insufficient same-date history | The fallback when fewer than ten prior valid same-month/day observations exist is not yet decided. |
| February 29 | Handling leap-day substitutions remains undecided. |
| Extended reporting gaps | Maximum acceptable consecutive gap, permissible age of historical same-date inputs, and handling prolonged outages under a fixed station set remain open. |
| Additional observations | Whether other observational archives are needed, and how to reconcile their station identities, units, quality flags and provenance with GHCN, remain open. A gap in GHCN does not prove that no observations exist elsewhere. |
| Final daily calculation | Station-level TMAX/TMIN combination, aggregation/weighting, day boundaries, reporting delays/revisions and uncertainty remain open under the established principles. |

## Completed experiments and findings

These are observations about specific runs. Findings and recommendations do not
by themselves adopt a final methodology.

### 1. First-pass metadata eligibility

The original filter requires both TMAX and TMIN inventory first years <=1926
and both last years >= the target year. The default target year is dynamic;
the saved live run used **2026**.

- Result: **1,640 stations**, across **35 NOAA country/territory codes**.
- Inventory endpoints establish neither continuous coverage nor paired daily
  observations. This stage does not assess day-by-day completeness or moves.
- Sources: [filter documentation](methodology.md#implemented-metadata-filter),
  [station CSV](../data/processed/eligibility/qualifying-stations.csv),
  [summary](../data/processed/eligibility/summary.json), and
  [provenance](../data/processed/eligibility/provenance.json).

### 2. Daily completeness over 100 years

The second-stage experiment examined **1926-01-01 through 2025-12-31**:
**36,525 days**, with no infilling. Both elements must be recorded and QC-valid
on the same date. Missing months and absent elements stay in the denominator.

- **704 of 1,640 stations** passed 95%, spanning **19 NOAA country/territory codes**.
- Median completeness was **93.666%** across candidates and **97.407%** among passers.
- Only **four** candidates had 100% completeness. A passing station could still
  have a **1,826-day** consecutive incomplete run: 95% is not strict continuity.
- Sources: [100-year methods](methodology.md#second-stage-daily-completeness),
  [implementation](../data-pipeline/src/temperature_pipeline/completeness.py),
  and [fixture-based tests](../data-pipeline/tests/test_completeness.py).
  Counts above were checked against the existing local
  `data/processed/completeness/summary.json`. That original run's output folder
  is ignored and not currently versioned; it is not linked as a permanent
  GitHub artifact. This log preserves the completed-run finding without claiming
  that those local files are committed.

### 3. The 50-year comparison and completeness thresholds

The exploratory comparison used first years <=1976, last years >=2026 and
**1976-01-01 through 2025-12-31**: **18,263 days**. It produced **5,243 candidates**.
Daily validity and exact-count threshold comparisons were unchanged.

| Minimum paired-valid completeness | Qualifying stations |
|---|---:|
| 70% | 3,992 |
| 75% | 3,868 |
| 80% | 3,725 |
| 85% | 3,476 |
| 90% | 3,008 |
| 95% | 2,202 |

At 95%, the pool covers **35 NOAA country/territory codes**. Changing the window
changes both initial eligibility and the completeness denominator; it is not a
simple relaxation of the earlier test and does not establish a preference for
recent observations. Country funnels were diagnostics, not political quotas.

The source results are permanently available as the
[frozen 50-year station metrics](../data/processed/geography/inputs/completeness-1976-2025.csv)
and their [source provenance](../data/processed/geography/inputs/source-provenance.json).
Threshold totals also reconcile with the
[geographic coverage table](../data/processed/geography/healpix/coverage.csv).

### 4. Equal-area HEALPix geographic coverage

The experiment used the 50-year candidates at all six thresholds, station
coordinates, HEALPix grids with **12, 48, 192 and 768 global cells**, and Natural
Earth 1:10m land polygons minus lakes. Antarctica and small mapped land fragments
were included. Coastal cells contributed their land area, not their entire area.

| Global cells | Land-containing cells | Occupied at 70% | Occupied at 85% | Occupied at 95% |
|---|---:|---:|---:|---:|
| 12 | 12 | 11 | 10 | 9 |
| 48 | 48 | 31 | 25 | 22 |
| 192 | 164 | 77 | 60 | 45 |
| 768 | 489 | 173 | 138 | 98 |

Key findings:

- Coarse cells hide gaps. At 70%, the 12-cell grid puts **98.8% of mapped land**
  in occupied cells, but random one-per-cell networks leave the median sampled
  land location about **2,598 km** from a station. Cell occupancy is a proxy,
  not proof that all land in a cell is well represented.
- At 768 cells, land in occupied cells falls from **43.2%** at 70% completeness
  to **22.6%** at 95%. Empty regions cannot be repaired by adding stations to
  already dense cells.
- Separate cells do not guarantee separation: candidates in different cells
  can be only **13.1 km** apart. Boundary clustering needs explicit consideration.
- Even the full candidate pool has substantial gaps: the land-distance 95th
  percentile is about **3,469 km** at 70% and **5,927 km** at 95%.
- The report recommends investigating **192 cells** as an intermediate scale
  and **768 cells** as a finer audit/larger-network option, with 48 as a coarse
  control. Exploring 70–85% alongside strict 90–95% controls is a recommendation,
  **not an adopted threshold or selection rule**.
- Random one-per-cell networks were seeded diagnostic simulations, not proposed
  or optimized final station sets. No political boundaries or temporal quality
  preferences entered the geographic calculations.
- Validation included 26 tests, geometric and sampling convergence checks,
  provenance/artifact checks, and byte-identical reproduction of all eight CSV
  tables. Land sampling used **3,588,564** equal-area pixel centers; tiny islands
  can be absent from that sample while still counted in polygon-based cell areas.

Sources and outputs:

- [Full report and tradeoffs](../data/processed/geography/healpix/report.md)
- [Methods, dependencies and reproduction commands](../analysis/healpix/README.md)
- [All resolutions and thresholds](../data/processed/geography/healpix/coverage.csv)
- [Per-cell land fractions and station counts](../data/processed/geography/healpix/cell-coverage.csv)
- [Station-to-cell assignments](../data/processed/geography/healpix/station-cell-assignments.csv)
- [Cross-cell spacing](../data/processed/geography/healpix/spacing.csv) and
  [neighboring-cell candidate pairs](../data/processed/geography/healpix/neighbor-cell-pairs.csv)
- [Land-to-nearest-station distributions](../data/processed/geography/healpix/land-nearest-station-distances.csv)
  and [one-per-cell simulation summaries](../data/processed/geography/healpix/one-per-cell-summary.csv)
- Maps (each shows 70%, 85%, 95%):
  [12 cells](../data/processed/geography/healpix/maps/healpix-12-cells.png),
  [48 cells](../data/processed/geography/healpix/maps/healpix-48-cells.png),
  [192 cells](../data/processed/geography/healpix/maps/healpix-192-cells.png),
  [768 cells](../data/processed/geography/healpix/maps/healpix-768-cells.png)
- [Provenance](../data/processed/geography/healpix/provenance.json),
  [validation](../data/processed/geography/healpix/validation.json), and
  [repeatability record](../data/processed/geography/healpix/repeatability.json)

## Status of this log

No final stations, historical window, completeness threshold, station count or
geographic optimization have been adopted by recording these experiments.
The provisional missing-day rule is not a change to the existing observation-only
completeness calculations. Future decisions should identify their status and
supporting evidence so experimental settings are not mistaken for settled rules.
