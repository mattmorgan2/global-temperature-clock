# Grid-free geographic station-network experiment

**Status: exploratory only. No final station network, completeness threshold, station count or methodology is adopted.**

The objective is mean great-circle distance from equal-area land sample locations to their nearest selected station. The same 1976–2025 eligibility results and land geometry as the previous HEALPix study are used. Completeness is only an eligibility filter. There are no political boundaries, country/continent/population quotas, coarse grid constraints or station-density weights in the objective. Antarctica is included. Geographic proximity is not proof of climatic representativeness.

## All 16 configurations

Distances below are evaluated against all **3,588,564** established equal-area land locations, not just training points. NN means each selected station’s nearest **other selected station**. All distances are kilometres.

| Completeness | Stations | Land mean | Land median | Land p90 | Land p95 | NN minimum | NN median | NN p90 | Chosen fit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 70% | 30 | 1,362.4 | 1,075.9 | 2,764.7 | 3,511.3 | 916.1 | 1,954.5 | 2,432.7 | training one-swap converged |
| 70% | 50 | 1,219.8 | 851.8 | 2,638.7 | 3,508.7 | 916.1 | 1,400.8 | 2,033.9 | training one-swap converged |
| 70% | 75 | 1,135.5 | 716.5 | 2,618.9 | 3,481.0 | 726.6 | 1,086.0 | 1,700.6 | 32-swap cap |
| 70% | 100 | 1,097.2 | 647.1 | 2,618.9 | 3,481.0 | 417.7 | 852.0 | 1,470.2 | 32-swap cap |
| 80% | 30 | 1,772.4 | 1,160.3 | 4,330.1 | 5,030.2 | 1,237.4 | 1,790.5 | 2,378.9 | training one-swap converged |
| 80% | 50 | 1,642.8 | 908.9 | 4,267.9 | 4,983.3 | 830.5 | 1,401.0 | 1,776.0 | training one-swap converged |
| 80% | 75 | 1,581.5 | 798.4 | 4,266.8 | 4,983.3 | 589.8 | 914.2 | 1,345.3 | 32-swap cap |
| 80% | 100 | 1,551.0 | 763.4 | 4,266.1 | 4,983.1 | 417.2 | 794.5 | 1,237.4 | 32-swap cap |
| 85% | 30 | 1,907.1 | 1,183.3 | 4,497.3 | 5,450.3 | 1,239.2 | 1,618.8 | 2,314.3 | training one-swap converged |
| 85% | 50 | 1,805.3 | 957.9 | 4,497.3 | 5,450.3 | 732.3 | 1,283.4 | 1,549.5 | training one-swap converged |
| 85% | 75 | 1,754.6 | 903.6 | 4,490.4 | 5,421.6 | 436.7 | 876.2 | 1,243.3 | 32-swap cap |
| 85% | 100 | 1,731.5 | 889.8 | 4,490.2 | 5,421.6 | 406.4 | 684.8 | 1,115.1 | 32-swap cap |
| 95% | 30 | 2,194.5 | 1,621.6 | 5,180.8 | 5,938.3 | 835.9 | 1,315.3 | 1,838.6 | training one-swap converged |
| 95% | 50 | 2,143.6 | 1,581.5 | 5,167.3 | 5,927.8 | 420.0 | 925.6 | 1,310.7 | training one-swap converged |
| 95% | 75 | 2,121.6 | 1,579.2 | 5,167.3 | 5,927.6 | 409.7 | 681.1 | 988.1 | training one-swap converged |
| 95% | 100 | 2,111.8 | 1,577.4 | 5,167.0 | 5,927.4 | 346.4 | 522.8 | 929.8 | 32-swap cap |

## Gains as stations are added

The search minimizes mean distance; tail distances and station separation are reported, not optimized. Networks at successive sizes are independent refined subsets and need not be nested.

| Completeness | Increase in size | Mean improvement | Mean improvement % | Improvement per added station | Change in land p95 |
|---|---|---:|---:|---:|---:|
| 70% | 30 → 50 | 142.6 km | 10.47% | 7.13 km | 2.6 km |
| 70% | 50 → 75 | 84.3 km | 6.91% | 3.37 km | 27.7 km |
| 70% | 75 → 100 | 38.3 km | 3.37% | 1.53 km | 0.0 km |
| 80% | 30 → 50 | 129.7 km | 7.32% | 6.48 km | 46.9 km |
| 80% | 50 → 75 | 61.3 km | 3.73% | 2.45 km | 0.0 km |
| 80% | 75 → 100 | 30.5 km | 1.93% | 1.22 km | 0.2 km |
| 85% | 30 → 50 | 101.8 km | 5.34% | 5.09 km | 0.0 km |
| 85% | 50 → 75 | 50.7 km | 2.81% | 2.03 km | 28.7 km |
| 85% | 75 → 100 | 23.1 km | 1.32% | 0.92 km | 0.0 km |
| 95% | 30 → 50 | 50.9 km | 2.32% | 2.55 km | 10.5 km |
| 95% | 50 → 75 | 22.0 km | 1.03% | 0.88 km | 0.2 km |
| 95% | 75 → 100 | 9.8 km | 0.46% | 0.39 km | 0.2 km |

Observed tradeoffs, without a final recommendation:

- At 70%, increasing 30 → 50 stations reduces mean distance by about **143 km (10.5%)**. The 75 → 100 increase improves it by only about **38 km (3.4%)**.
- At 95%, the corresponding improvements are about **51 km (2.3%)** and **10 km (0.46%)**. Much of the remaining gap is inherent in the eligible candidate geography.
- A 70% / 30-station trial has a lower mean distance (about **1,362 km**) than the 95% / 100-station trial (about **2,112 km**). This is a geographic comparison, not evidence that the missing observations at 70% are acceptable.
- Mean distances decline with network size in every threshold group. The p95 changes much less, approaching a floor created by candidate-free regions. Adding stations in available areas cannot create observations where eligible candidates are absent.
- Minimum station separation declines as more facilities are added. There is no separation constraint, and optimizing mean land distance does not optimize a regular station lattice.

## Full-candidate lower bounds

Using every eligible station gives an optimistic lower bound for any fixed-size subset, not a claim that the bound is attainable with 30–100 stations.

| Completeness | Eligible candidates | Full-pool mean lower bound | 30-station mean | 100-station mean | 100-station excess over lower bound |
|---|---:|---:|---:|---:|---:|
| 70% | 3992 | 1015.4 km | 1362.4 km | 1097.2 km | 81.8 km |
| 80% | 3725 | 1485.6 km | 1772.4 km | 1551.0 km | 65.4 km |
| 85% | 3476 | 1676.0 km | 1907.1 km | 1731.5 km | 55.5 km |
| 95% | 2202 | 2088.0 km | 2194.5 km | 2111.8 km | 23.7 km |

## Comparison with existing random one-per-cell HEALPix networks

Only the same completeness threshold and network sizes within **20%** are compared. Both methods are scored on the **same existing 100,000-point land subset**. Random values are medians across the prior 32 simulations. Sizes differ explicitly: these are practical benchmarks, not equal-budget proofs of superiority. There are no new random grid-network simulations in this experiment.

| Completeness | P-median size | HEALPix cells / random size | P-median mean | Random mean | Mean reduction | P-median p95 | Random p95 |
|---|---:|---|---:|---:|---:|---:|---:|
| 70% | 30 | 48 / 31 | 1362.0 km | 1753.5 km | 22.3% | 3509.8 km | 3735.5 km |
| 70% | 75 | 192 / 77 | 1135.6 km | 1296.5 km | 12.4% | 3474.9 km | 3511.1 km |
| 80% | 30 | 48 / 27 | 1780.4 km | 2236.3 km | 20.4% | 5036.3 km | 5475.4 km |
| 80% | 75 | 192 / 66 | 1588.3 km | 1809.9 km | 12.2% | 4985.9 km | 5130.0 km |
| 85% | 30 | 48 / 25 | 1913.9 km | 2396.0 km | 20.1% | 5460.2 km | 6024.7 km |
| 85% | 50 | 192 / 60 | 1811.3 km | 2019.8 km | 10.3% | 5460.2 km | 5839.0 km |
| 85% | 75 | 192 / 60 | 1760.8 km | 2019.8 km | 12.8% | 5436.3 km | 5839.0 km |
| 95% | 50 | 192 / 45 | 2149.0 km | 2475.3 km | 13.2% | 5918.0 km | 6598.7 km |
| 95% | 100 | 768 / 98 | 2117.4 km | 2167.6 km | 2.3% | 5917.8 km | 5948.8 km |

The closest size matches include 30 versus 31 stations at 70%, 75 versus 77 at 70%, and 100 versus 98 at 95%. Their mean reductions are about **22.3%, 12.4%, and 2.3%**, respectively. The grid-free search helps most when random cell membership leaves inefficient placements; its benefit becomes limited near the full-pool coverage floor. No grid resolution or final geographic method is chosen by these comparisons.

## Method, approximation and performance

1. Use the versioned 1976–2025 station metrics, preserving the 1976-start/2026-endpoint candidate rules. Filter by exact paired-valid day counts at 70/80/85/95%; no recency weighting or infilling.
2. Draw 16,384 land demand locations uniformly without replacement for each of two fits, using seeds 2026111301 and 2026111302. Both fits reuse their samples across thresholds and network sizes. Every sampled point has equal land-area weight. Coarse HEALPix cell IDs are never used in station selection.
3. Greedily add facilities that minimize the resulting mean distance. Refine each requested prefix with best-improving one-for-one swaps across every eligible addition/removal. Stop at a 0.0001-km training-mean improvement tolerance or 32 accepted swaps.
4. Evaluate both fits against the entire 3,588,564-location land sample and retain the lower full-sample mean for each configuration. Sort retained members by chronological entry into that fit; preserve selection/swap history in CSVs.
- Runtime of the full run: **239.9 seconds** (4.0 minutes), including full-sample scoring and rendering. Largest distance matrix: **249.5 MiB**, not total peak process memory. A full all-candidate/all-land matrix would require about 57 GB before search overhead.
- **21 of 32** fitted restart configurations reached training one-swap convergence. **7 of the 16** retained trials hit the swap cap. Negative remaining training improvements are recorded; no global optimum is claimed.
- The largest full-sample mean difference between the two fits of the same configuration was **3.99 km**; median difference was **0.48 km**. This measures two-seed sensitivity, not a complete uncertainty bound.
- Distance storage is float32 kilometres, with float64 objective reductions; this introduces approximately metre-scale storage precision. Ties use stable station-ID order only. Completeness never enters the score or tie resolution.
- The training subsets approximate the objective. Exact global optimization was not attempted; a converged training fit can remain suboptimal on the full land sample. The 32-swap cap also limits some fits.
- The land mask and NSIDE 1024 sampling are unchanged: Natural Earth land minus lakes, including Antarctica. Fine pixels are about 40.54 km²; tiny islands may have no demand point. Coastline and sampling approximations carry over from the HEALPix report.
- Mean-distance optimization can allocate additional facilities in well-sampled areas when the candidate pool offers no way to improve large empty regions. This is an objective-driven marginal gain, not a quota or compensation for empty cells, and does not establish uniform or climatic representation.
- Prior HEALPix benchmarks were random, not optimized within cells, and have different station counts. Their comparison cannot isolate grid-boundary effects from search quality or budget differences.

## Validation

- Nine new unit tests cover greedy mean-distance behavior, dense-candidate duplicates, deterministic ties, swap deltas versus brute force, unique counts, objective improvement, swap caps, spherical distances and map-panel marker isolation.
- Every final network was independently rescored at all 3,588,564 land locations using independently constructed spherical vectors. Maximum discrepancy in the seven requested distance metrics was **1.82e-12 km**.
- All selected metadata match the frozen source exactly; IDs are unique and satisfy the applicable completeness threshold. Training sample indices reproduce from their seeds. Each 30-station chosen fit was replayed and reproduced its station IDs.
- All full-sample mean distances exceed their full-candidate lower bounds; mean distance improves with network size in each threshold group. Output hashes and map integrity are checked. Every map panel contains exactly its requested number of station markers.
- Existing eligibility/completeness code and decision/methodology documents are unchanged. No commit or push is part of this experiment.

## Files for review

- [All 16 metrics](comparison.csv), [both fits](restart-results.csv), [selection trace](selection-trace.csv), [incremental runtime records](performance.csv), and [HEALPix comparison](healpix-comparison.csv).
- [Coverage improvement chart](coverage-improvement.png) (also PDF).
- Maps, each containing all four requested network sizes: [70%](maps/networks-70pct.png), [80%](maps/networks-80pct.png), [85%](maps/networks-85pct.png), [95%](maps/networks-95pct.png) (also PDFs).
- The `networks/` directory contains all 16 selected-station CSVs; [combined selected-station rows](selected-stations-all-networks.csv) are also provided. They are explicitly marked `is_final_network=False`.
- [Numerical validation](validation.json), [independent validation](independent-validation.json), [map validation](map-validation.json), and [provenance](provenance.json).
- Reproducible code, tests, dependency reference and detailed methods: `analysis/facility_location/README.md`.
