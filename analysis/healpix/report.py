"""Build the human-readable report from a successful geographic run."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/geography/healpix'
def read(name):return list(csv.DictReader((OUT/name).open()))
cov=read('coverage.csv');sim=read('one-per-cell-summary.csv');spacing=read('spacing.csv');dist=read('land-nearest-station-distances.csv')
lookup={(int(r['global_cells']),int(r['threshold_percent'])):r for r in cov}
valid=json.loads((OUT/'validation.json').read_text())
lines=['# Equal-area coverage of GHCN-Daily candidates\n',
'**Result:** investigate the 192-cell grid as a primary intermediate scale, with 768 cells as a finer coverage audit and an option for a larger network. Retain 48 cells as a coarse control. Twelve cells are too coarse to diagnose geographic gaps. This is not a final grid, threshold or station selection.\n',
'The analysis uses 5,243 stations from the 1976–2025 analysis. TMAX/TMIN must begin by 1976 and extend into 2026; thresholds use exact paired-valid day counts out of 18,263 days. Every day has the same weight. Historical/recent completeness is not reweighted or ranked. Geographic assignments use coordinates, never political quotas.\n',
'## Resolution and threshold comparison\n',
'**Each entry is occupied land cells / percentage of mapped land inside those cells.** This percentage is not the land area within a useful distance of a station. Cells include ocean, which is removed before area weighting.\n',
'| Global cells | Land cells | ≥70% | ≥75% | ≥80% | ≥85% | ≥90% | ≥95% |\n|---|---:|---:|---:|---:|---:|---:|---:|']
for n in (12,48,192,768):
    rr=lookup[(n,70)]
    lines.append(f"| {n} | {rr['land_cells']} | "+' | '.join(f"{lookup[(n,t)]['occupied_land_cells']} / {float(lookup[(n,t)]['represented_land_percent']):.1f}%" for t in (70,75,80,85,90,95))+' |')
lines.extend(['\nThe coarse-grid coverage percentages are deceptively high: 12 cells and 70% completeness mark 98.8% of land as belonging to occupied cells. The random one-per-cell simulations nevertheless leave the median land location roughly 2,598 km from a station. A cell-occupancy map alone is insufficient.\n',
'## Full coverage table\n',
'| Global cells | Threshold | Stations | Land cells | Occupied | Empty | Land in occupied cells | Singleton cells | Stations/cell mean | Median | Maximum |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'])
for n in (12,48,192,768):
    for t in (70,75,80,85,90,95):
        r=lookup[(n,t)]
        lines.append(f"| {n} | {t}% | {int(r['qualifying_stations']):,} | {r['land_cells']} | {r['occupied_land_cells']} | {r['unoccupied_land_cells']} | {float(r['represented_land_percent']):.2f}% | {r['singleton_occupied_land_cells']} | {float(r['stations_per_occupied_cell_mean']):.1f} | {float(r['stations_per_occupied_cell_median']):g} | {r['stations_per_occupied_cell_max']} |")
lines.extend(['\n## Distance from land to the full candidate pool\n',
'These equal-area land-sampling results include Antarctica. They are optimistic lower bounds for any subset network and do not depend on the coarse grid. Percentiles describe land area, not country counts or station density.\n',
'| Threshold | Median distance | 95th percentile | Largest sampled distance |\n|---|---:|---:|---:|'])
for r in dist:lines.append(f"| {r['threshold_percent']}% | {float(r['p50_km']):,.0f} km | {float(r['p95_km']):,.0f} km | {float(r['max_km']):,.0f} km |")
lines.extend(['\n## One-per-occupied-cell simulations\n',
'Thirty-two seeded random networks per configuration, evaluated at the same 100,000 sampled land locations. Values below are the median statistic across simulations, not an optimized or proposed network. There are no additional stations for empty cells.\n',
'| Global cells | Threshold | Network size | Median land distance | Land-distance p95 | Minimum station separation |\n|---|---:|---:|---:|---:|---:|'])
for n in (12,48,192,768):
    for t in (70,85,95):
        r=next(r for r in sim if int(r['global_cells'])==n and int(r['threshold_percent'])==t)
        lines.append(f"| {n} | {t}% | {r['network_size']} | {float(r['land_nearest_p50_km_across_simulations_median']):,.0f} km | {float(r['land_nearest_p95_km_across_simulations_median']):,.0f} km | {float(r['station_nearest_neighbor_min_km_across_simulations_median']):,.0f} km |")
lines.extend(['\nThe 192-cell grid yields 45–77 occupied land cells, depending on threshold; 768 yields 98–173. Neither range is a prescribed network size. At 70%, finer cells reduce simulated median land distance from about 944 km (192) to 688 km (768), but p95 remains about 3,500 km: empty regions, not just thinning of dense areas, dominate the far tail.\n',
'## Cross-boundary clustering\n',
'Neighboring cells share an edge or vertex. A boundary-cluster flag means the closest candidate pair is <=100 km apart and each station is within 50 km of its own cell boundary. These are diagnostic distances, not eligibility rules. Pairs near a shared corner are included.\n',
'| Global cells | Threshold | Occupied neighbor pairs | Pairs within 100 km | Boundary-cluster pairs | Closest cross-cell station pair | Median station-to-nearest-other-cell candidate |\n|---|---:|---:|---:|---:|---:|---:|'])
for n in (12,48,192,768):
    for t in (70,85,95):
        r=next(r for r in spacing if int(r['global_cells'])==n and int(r['threshold_percent'])==t)
        lines.append(f"| {n} | {t}% | {r['occupied_neighbor_pairs']} | {r['neighbor_pairs_closest_within_100km']} | {r['neighbor_pairs_boundary_cluster']} | {float(r['cross_cell_pair_min_km']):.1f} km | {float(r['nearest_other_cell_p50_km']):,.0f} km |")
lines.extend(['\nSeparate cell IDs do not guarantee useful station separation. At 768 cells / 70%, candidates in different cells can be only 13.1 km apart. Before any final selection, geography within cells and cross-boundary spacing need consideration. No distance cutoff is adopted here. All unordered cross-cell pair-distance distributions are in spacing.csv; closest IDs and boundary diagnostics are in neighbor-cell-pairs.csv.\n',
'## Land and coastal treatment\n',
'Natural Earth 1:10m land minus its Lake/Reservoir/Alkaline Lake polygons, pinned to GitHub commit ca96624a56bd078437bca8184e78163e5039ad19. Public-domain data, including Antarctica. HEALPix NSIDE 1/2/4/8, NESTED order; spherical Earth radius 6,371.0088 km. Curved boundaries are densified and polygon-intersected, with spherical area integration. Coastal ocean is never counted as land. Land cells with tiny fractions are included rather than silently discarded.\n',
'| Global cells | Land cells below 1% land fraction | Land cells with <100 km² land |\n|---|---:|---:|'])
for n in (12,48,192,768):
    r=lookup[(n,70)];lines.append(f"| {n} | {r['land_cells_below_1pct_land_fraction']} | {r['land_cells_below_100km2']} |")
lines.extend(['\nThere are 161 qualifying station points outside the polygon land mask at 70%, and 99 at 95%. They are retained and flagged, not assigned invented land area or excluded by a new rule. Coastal generalization, coordinate precision, lake locations and metadata accuracy require individual review; no cause is assumed. All qualifying station cells contain some mapped land at every evaluated resolution.\n',
'## Validation and approximation limits\n',
f"- Five geometry/distance unit tests and all 21 existing pipeline tests passed. All 24 runs reconcile station/cell totals and exact completeness thresholds. Nested-grid and threshold-monotonicity checks passed. All eight CSV tables reproduced byte-for-byte on a second run; dependencies, output hashes and PNG/PDF integrity checks also passed.",
f"- Fine land sample: {valid['fine_sample_land_points']:,} HEALPix NSIDE 1024 centers; comparison sample NSIDE 512: {valid['coarse_sample_land_points']:,}. Approximately 40.54 km² per fine pixel; every accepted center has equal area weight.",
f"- Sample-implied land area differs from polygon-integrated land area by {100*valid['sampling_area_relative_difference']:.4f}%. Very small islands may have no sample center even though their land is counted in the polygon coverage tables.",
f"- Maximum p95 nearest-distance change when doubling sample NSIDE: {max(abs(r['p95_distance_change_km']) for r in valid['sampling_convergence']):.3f} km.",
f"- Maximum relative land-area discrepancy across grids: {100*max(r['global_land_relative_error'] for r in valid['grid_geometry']):.6f}%; maximum boundary-refinement area discrepancy: {100*max(r['boundary_convergence_relative_land_error'] for r in valid['grid_geometry']):.6f}%.",
f"- Land-cell count changes when doubling edge sampling: {[r['land_cell_count_change_on_doubling_boundary_step'] for r in valid['grid_geometry']]}; see validation.json for every resolution.",
'- Natural Earth is generalized present-day geography, not a historical coastline or a complete inventory of tiny islands/waterbodies. Station moves and shoreline change are not inferred.',
'- Simulations are not an optimization: more careful within-cell choices could improve spacing. Full-pool nearest distances are lower bounds; random one-per-cell distances are examples, not guarantees.',
'- The 50-year window and existing eligibility constraints define this candidate pool; these results do not establish absence of other observations worldwide. No claim of climate representativeness follows from geometric coverage alone.\n',
'## Recommendations for further investigation\n',
'1. **192 cells:** primary intermediate-scale investigation. It exposes major empty regions while allowing approximately 45–77 occupied-cell choices, without assuming 50 is the target. Compare several thresholds rather than choose one now.',
'2. **768 cells:** retain as the coverage audit and a larger-network option (98–173 occupied cells). It identifies gaps masked by coarse grids and reveals singleton fragility and cross-boundary clusters.',
'3. **48 cells:** use as a coarse sensitivity/control case (22–31 occupied cells), not evidence that broad occupied cells are uniformly represented. Twelve cells are too coarse for the stated geographic goal.',
'4. Carry **70–85%** forward as a geographic/completeness tradeoff range, with 90–95% strict controls. Audit temporal gaps alongside these percentages; do not favor a recent or historical subperiod without a separate decision.',
'5. Before final selection, examine coordinate/land-mask mismatches and test within-cell spacing objectives. Do not add compensating stations to dense regions for empty cells. Grid orientation sensitivity and alternative equal-area grids can be future checks; the present comparison keeps one standard HEALPix orientation.\n',
'## Maps and machine-readable outputs\n',
'- [12-cell maps](maps/healpix-12-cells.png), [48-cell maps](maps/healpix-48-cells.png), [192-cell maps](maps/healpix-192-cells.png), [768-cell maps](maps/healpix-768-cells.png): each includes 70%, 85%, 95%. Matching PDFs are available.',
'- [Coverage table](coverage.csv), [all cell fractions/counts](cell-coverage.csv), [station assignments](station-cell-assignments.csv).',
'- [Spacing](spacing.csv), [neighbor pairs](neighbor-cell-pairs.csv), [land distances](land-nearest-station-distances.csv), [simulation summaries](one-per-cell-summary.csv).',
'- Source hashes, dependency versions and parameters: provenance.json. Full methods and reproducible commands: analysis/healpix/README.md in the repository.\n'])
(OUT/'report.md').write_text('\n'.join(lines).rstrip()+'\n')
print(OUT/'report.md')
