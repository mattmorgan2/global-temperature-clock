# Equal-area coverage of GHCN-Daily candidates

**Result:** investigate the 192-cell grid as a primary intermediate scale, with 768 cells as a finer coverage audit and an option for a larger network. Retain 48 cells as a coarse control. Twelve cells are too coarse to diagnose geographic gaps. This is not a final grid, threshold or station selection.

The analysis uses 5,243 stations from the 1976–2025 analysis. TMAX/TMIN must begin by 1976 and extend into 2026; thresholds use exact paired-valid day counts out of 18,263 days. Every day has the same weight. Historical/recent completeness is not reweighted or ranked. Geographic assignments use coordinates, never political quotas.

## Resolution and threshold comparison

**Each entry is occupied land cells / percentage of mapped land inside those cells.** This percentage is not the land area within a useful distance of a station. Cells include ocean, which is removed before area weighting.

| Global cells | Land cells | ≥70% | ≥75% | ≥80% | ≥85% | ≥90% | ≥95% |
|---|---:|---:|---:|---:|---:|---:|---:|
| 12 | 12 | 11 / 98.8% | 11 / 98.8% | 10 / 90.8% | 10 / 90.8% | 9 / 84.8% | 9 / 84.8% |
| 48 | 48 | 31 / 83.3% | 29 / 77.4% | 27 / 70.6% | 25 / 69.4% | 24 / 67.5% | 22 / 57.4% |
| 192 | 164 | 77 / 63.9% | 70 / 57.8% | 66 / 54.1% | 60 / 51.0% | 56 / 46.3% | 45 / 33.1% |
| 768 | 489 | 173 / 43.2% | 157 / 40.1% | 150 / 38.3% | 138 / 35.5% | 122 / 30.3% | 98 / 22.6% |

The coarse-grid coverage percentages are deceptively high: 12 cells and 70% completeness mark 98.8% of land as belonging to occupied cells. The random one-per-cell simulations nevertheless leave the median land location roughly 2,598 km from a station. A cell-occupancy map alone is insufficient.

## Full coverage table

| Global cells | Threshold | Stations | Land cells | Occupied | Empty | Land in occupied cells | Singleton cells | Stations/cell mean | Median | Maximum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 70% | 3,992 | 12 | 11 | 1 | 98.82% | 0 | 362.9 | 103 | 1590 |
| 12 | 75% | 3,868 | 12 | 11 | 1 | 98.82% | 1 | 351.6 | 100 | 1545 |
| 12 | 80% | 3,725 | 12 | 10 | 2 | 90.82% | 0 | 372.5 | 140.5 | 1485 |
| 12 | 85% | 3,476 | 12 | 10 | 2 | 90.82% | 1 | 347.6 | 128.5 | 1376 |
| 12 | 90% | 3,008 | 12 | 9 | 3 | 84.84% | 0 | 334.2 | 137 | 1206 |
| 12 | 95% | 2,202 | 12 | 9 | 3 | 84.84% | 0 | 244.7 | 97 | 822 |
| 48 | 70% | 3,992 | 48 | 31 | 17 | 83.26% | 4 | 128.8 | 10 | 1525 |
| 48 | 75% | 3,868 | 48 | 29 | 19 | 77.44% | 5 | 133.4 | 10 | 1482 |
| 48 | 80% | 3,725 | 48 | 27 | 21 | 70.64% | 4 | 138.0 | 14 | 1430 |
| 48 | 85% | 3,476 | 48 | 25 | 23 | 69.41% | 3 | 139.0 | 14 | 1326 |
| 48 | 90% | 3,008 | 48 | 24 | 24 | 67.50% | 2 | 125.3 | 10.5 | 1160 |
| 48 | 95% | 2,202 | 48 | 22 | 26 | 57.43% | 4 | 100.1 | 10 | 783 |
| 192 | 70% | 3,992 | 164 | 77 | 87 | 63.85% | 17 | 51.8 | 4 | 774 |
| 192 | 75% | 3,868 | 164 | 70 | 94 | 57.82% | 14 | 55.3 | 5.5 | 760 |
| 192 | 80% | 3,725 | 164 | 66 | 98 | 54.15% | 12 | 56.4 | 6 | 740 |
| 192 | 85% | 3,476 | 164 | 60 | 104 | 51.03% | 11 | 57.9 | 7 | 706 |
| 192 | 90% | 3,008 | 164 | 56 | 108 | 46.28% | 11 | 53.7 | 5 | 638 |
| 192 | 95% | 2,202 | 164 | 45 | 119 | 33.06% | 11 | 48.9 | 6 | 462 |
| 768 | 70% | 3,992 | 489 | 173 | 316 | 43.23% | 63 | 23.1 | 3 | 304 |
| 768 | 75% | 3,868 | 489 | 157 | 332 | 40.12% | 52 | 24.6 | 3 | 299 |
| 768 | 80% | 3,725 | 489 | 150 | 339 | 38.29% | 48 | 24.8 | 3 | 294 |
| 768 | 85% | 3,476 | 489 | 138 | 351 | 35.49% | 42 | 25.2 | 4 | 288 |
| 768 | 90% | 3,008 | 489 | 122 | 367 | 30.30% | 40 | 24.7 | 3 | 259 |
| 768 | 95% | 2,202 | 489 | 98 | 391 | 22.62% | 33 | 22.5 | 4 | 199 |

## Distance from land to the full candidate pool

These equal-area land-sampling results include Antarctica. They are optimistic lower bounds for any subset network and do not depend on the coarse grid. Percentiles describe land area, not country counts or station density.

| Threshold | Median distance | 95th percentile | Largest sampled distance |
|---|---:|---:|---:|
| 70% | 595 km | 3,469 km | 5,154 km |
| 75% | 704 km | 3,903 km | 5,269 km |
| 80% | 743 km | 4,979 km | 7,523 km |
| 85% | 872 km | 5,421 km | 8,625 km |
| 90% | 1,037 km | 5,919 km | 8,715 km |
| 95% | 1,575 km | 5,927 km | 8,715 km |

## One-per-occupied-cell simulations

Thirty-two seeded random networks per configuration, evaluated at the same 100,000 sampled land locations. Values below are the median statistic across simulations, not an optimized or proposed network. There are no additional stations for empty cells.

| Global cells | Threshold | Network size | Median land distance | Land-distance p95 | Minimum station separation |
|---|---:|---:|---:|---:|---:|
| 12 | 70% | 11 | 2,598 km | 5,123 km | 980 km |
| 12 | 85% | 10 | 2,890 km | 7,214 km | 835 km |
| 12 | 95% | 9 | 3,043 km | 7,427 km | 1,063 km |
| 48 | 70% | 31 | 1,581 km | 3,736 km | 126 km |
| 48 | 85% | 25 | 1,971 km | 6,025 km | 86 km |
| 48 | 95% | 22 | 2,145 km | 6,741 km | 350 km |
| 192 | 70% | 77 | 944 km | 3,511 km | 102 km |
| 192 | 85% | 60 | 1,241 km | 5,839 km | 124 km |
| 192 | 95% | 45 | 1,869 km | 6,599 km | 284 km |
| 768 | 70% | 173 | 688 km | 3,508 km | 88 km |
| 768 | 85% | 138 | 1,003 km | 5,512 km | 95 km |
| 768 | 95% | 98 | 1,648 km | 5,949 km | 134 km |

The 192-cell grid yields 45–77 occupied land cells, depending on threshold; 768 yields 98–173. Neither range is a prescribed network size. At 70%, finer cells reduce simulated median land distance from about 944 km (192) to 688 km (768), but p95 remains about 3,500 km: empty regions, not just thinning of dense areas, dominate the far tail.

## Cross-boundary clustering

Neighboring cells share an edge or vertex. A boundary-cluster flag means the closest candidate pair is <=100 km apart and each station is within 50 km of its own cell boundary. These are diagnostic distances, not eligibility rules. Pairs near a shared corner are included.

| Global cells | Threshold | Occupied neighbor pairs | Pairs within 100 km | Boundary-cluster pairs | Closest cross-cell station pair | Median station-to-nearest-other-cell candidate |
|---|---:|---:|---:|---:|---:|---:|
| 12 | 70% | 30 | 5 | 5 | 19.2 km | 785 km |
| 12 | 85% | 25 | 4 | 4 | 19.2 km | 748 km |
| 12 | 95% | 21 | 4 | 4 | 24.5 km | 732 km |
| 48 | 70% | 84 | 10 | 8 | 19.2 km | 598 km |
| 48 | 85% | 63 | 7 | 6 | 19.2 km | 583 km |
| 48 | 95% | 52 | 5 | 4 | 24.5 km | 594 km |
| 192 | 70% | 194 | 21 | 18 | 13.1 km | 292 km |
| 192 | 85% | 140 | 18 | 16 | 18.3 km | 292 km |
| 192 | 95% | 82 | 14 | 12 | 18.3 km | 305 km |
| 768 | 70% | 406 | 69 | 58 | 13.1 km | 164 km |
| 768 | 85% | 328 | 61 | 51 | 14.7 km | 164 km |
| 768 | 95% | 220 | 48 | 41 | 18.3 km | 177 km |

Separate cell IDs do not guarantee useful station separation. At 768 cells / 70%, candidates in different cells can be only 13.1 km apart. Before any final selection, geography within cells and cross-boundary spacing need consideration. No distance cutoff is adopted here. All unordered cross-cell pair-distance distributions are in spacing.csv; closest IDs and boundary diagnostics are in neighbor-cell-pairs.csv.

## Land and coastal treatment

Natural Earth 1:10m land minus its Lake/Reservoir/Alkaline Lake polygons, pinned to GitHub commit ca96624a56bd078437bca8184e78163e5039ad19. Public-domain data, including Antarctica. HEALPix NSIDE 1/2/4/8, NESTED order; spherical Earth radius 6,371.0088 km. Curved boundaries are densified and polygon-intersected, with spherical area integration. Coastal ocean is never counted as land. Land cells with tiny fractions are included rather than silently discarded.

| Global cells | Land cells below 1% land fraction | Land cells with <100 km² land |
|---|---:|---:|
| 12 | 0 | 0 |
| 48 | 12 | 1 |
| 192 | 50 | 19 |
| 768 | 115 | 55 |

There are 161 qualifying station points outside the polygon land mask at 70%, and 99 at 95%. They are retained and flagged, not assigned invented land area or excluded by a new rule. Coastal generalization, coordinate precision, lake locations and metadata accuracy require individual review; no cause is assumed. All qualifying station cells contain some mapped land at every evaluated resolution.

## Validation and approximation limits

- Five geometry/distance unit tests and all 21 existing pipeline tests passed. All 24 runs reconcile station/cell totals and exact completeness thresholds. Nested-grid and threshold-monotonicity checks passed. All eight CSV tables reproduced byte-for-byte on a second run; dependencies, output hashes and PNG/PDF integrity checks also passed.
- Fine land sample: 3,588,564 HEALPix NSIDE 1024 centers; comparison sample NSIDE 512: 897,131. Approximately 40.54 km² per fine pixel; every accepted center has equal area weight.
- Sample-implied land area differs from polygon-integrated land area by -0.0029%. Very small islands may have no sample center even though their land is counted in the polygon coverage tables.
- Maximum p95 nearest-distance change when doubling sample NSIDE: 0.558 km.
- Maximum relative land-area discrepancy across grids: 0.000000%; maximum boundary-refinement area discrepancy: 0.000565%.
- Land-cell count changes when doubling edge sampling: [0, 0, 0, 0]; see validation.json for every resolution.
- Natural Earth is generalized present-day geography, not a historical coastline or a complete inventory of tiny islands/waterbodies. Station moves and shoreline change are not inferred.
- Simulations are not an optimization: more careful within-cell choices could improve spacing. Full-pool nearest distances are lower bounds; random one-per-cell distances are examples, not guarantees.
- The 50-year window and existing eligibility constraints define this candidate pool; these results do not establish absence of other observations worldwide. No claim of climate representativeness follows from geometric coverage alone.

## Recommendations for further investigation

1. **192 cells:** primary intermediate-scale investigation. It exposes major empty regions while allowing approximately 45–77 occupied-cell choices, without assuming 50 is the target. Compare several thresholds rather than choose one now.
2. **768 cells:** retain as the coverage audit and a larger-network option (98–173 occupied cells). It identifies gaps masked by coarse grids and reveals singleton fragility and cross-boundary clusters.
3. **48 cells:** use as a coarse sensitivity/control case (22–31 occupied cells), not evidence that broad occupied cells are uniformly represented. Twelve cells are too coarse for the stated geographic goal.
4. Carry **70–85%** forward as a geographic/completeness tradeoff range, with 90–95% strict controls. Audit temporal gaps alongside these percentages; do not favor a recent or historical subperiod without a separate decision.
5. Before final selection, examine coordinate/land-mask mismatches and test within-cell spacing objectives. Do not add compensating stations to dense regions for empty cells. Grid orientation sensitivity and alternative equal-area grids can be future checks; the present comparison keeps one standard HEALPix orientation.

## Maps and machine-readable outputs

- [12-cell maps](maps/healpix-12-cells.png), [48-cell maps](maps/healpix-48-cells.png), [192-cell maps](maps/healpix-192-cells.png), [768-cell maps](maps/healpix-768-cells.png): each includes 70%, 85%, 95%. Matching PDFs are available.
- [Coverage table](coverage.csv), [all cell fractions/counts](cell-coverage.csv), [station assignments](station-cell-assignments.csv).
- [Spacing](spacing.csv), [neighbor pairs](neighbor-cell-pairs.csv), [land distances](land-nearest-station-distances.csv), [simulation summaries](one-per-cell-summary.csv).
- Source hashes, dependency versions and parameters: provenance.json. Full methods and reproducible commands: analysis/healpix/README.md in the repository.
