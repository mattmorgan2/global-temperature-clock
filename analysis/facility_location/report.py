"""Report the 16 exploratory p-median configurations without adopting a network."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np


def main(out):
    out=Path(out)
    rows=list(csv.DictReader((out/'comparison.csv').open()))
    restarts=list(csv.DictReader((out/'restart-results.csv').open()))
    baseline=list(csv.DictReader((out/'healpix-comparison.csv').open()))
    provenance=json.loads((out/'provenance.json').read_text())
    validation=json.loads((out/'validation.json').read_text())
    independent=json.loads((out/'independent-validation.json').read_text())
    by={(int(r['threshold_percent']),int(r['network_size'])):r for r in rows}
    combined=[]
    for r in rows:
        combined.extend(csv.DictReader((out/'networks'/f"network-{r['threshold_percent']}pct-{r['network_size']}.csv").open()))
    with (out/'selected-stations-all-networks.csv').open('w',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=list(combined[0]));writer.writeheader();writer.writerows(combined)
    seed_spreads=[]
    for threshold in (70,80,85,95):
        for count in (30,50,75,100):
            rr=[r for r in restarts if int(r['threshold_percent'])==threshold and int(r['network_size'])==count]
            means=[float(r['land_mean_km']) for r in rr]
            seed_spreads.append(max(means)-min(means))
    capped=sum(r['one_swap_converged']=='False' for r in rows)
    lines=['# Grid-free geographic station-network experiment\n',
    '**Status: exploratory only. No final station network, completeness threshold, station count or methodology is adopted.**\n',
    'The objective is mean great-circle distance from equal-area land sample locations to their nearest selected station. The same 1976–2025 eligibility results and land geometry as the previous HEALPix study are used. Completeness is only an eligibility filter. There are no political boundaries, country/continent/population quotas, coarse grid constraints or station-density weights in the objective. Antarctica is included. Geographic proximity is not proof of climatic representativeness.\n',
    '## All 16 configurations\n',
    'Distances below are evaluated against all **3,588,564** established equal-area land locations, not just training points. NN means each selected station’s nearest **other selected station**. All distances are kilometres.\n',
    '| Completeness | Stations | Land mean | Land median | Land p90 | Land p95 | NN minimum | NN median | NN p90 | Chosen fit |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in rows:
        fields=['land_mean_km','land_p50_km','land_p90_km','land_p95_km','station_nn_min_km','station_nn_p50_km','station_nn_p90_km']
        status='training one-swap converged' if r['one_swap_converged']=='True' else '32-swap cap'
        lines.append(f"| {r['threshold_percent']}% | {r['network_size']} | "+' | '.join(f'{float(r[k]):,.1f}' for k in fields)+f' | {status} |')
    lines.extend(['\n## Gains as stations are added\n',
    'The search minimizes mean distance; tail distances and station separation are reported, not optimized. Networks at successive sizes are independent refined subsets and need not be nested.\n',
    '| Completeness | Increase in size | Mean improvement | Mean improvement % | Improvement per added station | Change in land p95 |\n|---|---|---:|---:|---:|---:|'])
    for threshold in (70,80,85,95):
        for before,after in ((30,50),(50,75),(75,100)):
            a,b=by[(threshold,before)],by[(threshold,after)]
            gain=float(a['land_mean_km'])-float(b['land_mean_km'])
            tail=float(a['land_p95_km'])-float(b['land_p95_km'])
            lines.append(f'| {threshold}% | {before} → {after} | {gain:.1f} km | {100*gain/float(a["land_mean_km"]):.2f}% | {gain/(after-before):.2f} km | {tail:.1f} km |')
    lines.extend(['\nObserved tradeoffs, without a final recommendation:\n',
    '- At 70%, increasing 30 → 50 stations reduces mean distance by about **143 km (10.5%)**. The 75 → 100 increase improves it by only about **38 km (3.4%)**.',
    '- At 95%, the corresponding improvements are about **51 km (2.3%)** and **10 km (0.46%)**. Much of the remaining gap is inherent in the eligible candidate geography.',
    '- A 70% / 30-station trial has a lower mean distance (about **1,362 km**) than the 95% / 100-station trial (about **2,112 km**). This is a geographic comparison, not evidence that the missing observations at 70% are acceptable.',
    '- Mean distances decline with network size in every threshold group. The p95 changes much less, approaching a floor created by candidate-free regions. Adding stations in available areas cannot create observations where eligible candidates are absent.',
    '- Minimum station separation declines as more facilities are added. There is no separation constraint, and optimizing mean land distance does not optimize a regular station lattice.\n',
    '## Full-candidate lower bounds\n',
    'Using every eligible station gives an optimistic lower bound for any fixed-size subset, not a claim that the bound is attainable with 30–100 stations.\n',
    '| Completeness | Eligible candidates | Full-pool mean lower bound | 30-station mean | 100-station mean | 100-station excess over lower bound |\n|---|---:|---:|---:|---:|---:|'])
    for threshold in (70,80,85,95):
        a,b=by[(threshold,30)],by[(threshold,100)]
        lines.append(f"| {threshold}% | {a['candidate_count']} | {float(a['full_candidate_pool_mean_lower_bound_km']):.1f} km | {float(a['land_mean_km']):.1f} km | {float(b['land_mean_km']):.1f} km | {float(b['mean_above_full_pool_km']):.1f} km |")
    lines.extend(['\n## Comparison with existing random one-per-cell HEALPix networks\n',
    'Only the same completeness threshold and network sizes within **20%** are compared. Both methods are scored on the **same existing 100,000-point land subset**. Random values are medians across the prior 32 simulations. Sizes differ explicitly: these are practical benchmarks, not equal-budget proofs of superiority. There are no new random grid-network simulations in this experiment.\n',
    '| Completeness | P-median size | HEALPix cells / random size | P-median mean | Random mean | Mean reduction | P-median p95 | Random p95 |\n|---|---:|---|---:|---:|---:|---:|---:|'])
    for r in baseline:
        opt=float(r['optimized_mean_same_sample_km']);base=float(r['random_mean_median_km'])
        lines.append(f"| {r['threshold_percent']}% | {r['optimized_network_size']} | {r['healpix_global_cells']} / {r['healpix_network_size']} | {opt:.1f} km | {base:.1f} km | {100*(base-opt)/base:.1f}% | {float(r['optimized_p95_same_sample_km']):.1f} km | {float(r['random_p95_median_km']):.1f} km |")
    lines.extend(['\nThe closest size matches include 30 versus 31 stations at 70%, 75 versus 77 at 70%, and 100 versus 98 at 95%. Their mean reductions are about **22.3%, 12.4%, and 2.3%**, respectively. The grid-free search helps most when random cell membership leaves inefficient placements; its benefit becomes limited near the full-pool coverage floor. No grid resolution or final geographic method is chosen by these comparisons.\n',
    '## Method, approximation and performance\n',
    '1. Use the versioned 1976–2025 station metrics, preserving the 1976-start/2026-endpoint candidate rules. Filter by exact paired-valid day counts at 70/80/85/95%; no recency weighting or infilling.',
    '2. Draw 16,384 land demand locations uniformly without replacement for each of two fits, using seeds 2026111301 and 2026111302. Both fits reuse their samples across thresholds and network sizes. Every sampled point has equal land-area weight. Coarse HEALPix cell IDs are never used in station selection.',
    '3. Greedily add facilities that minimize the resulting mean distance. Refine each requested prefix with best-improving one-for-one swaps across every eligible addition/removal. Stop at a 0.0001-km training-mean improvement tolerance or 32 accepted swaps.',
    '4. Evaluate both fits against the entire 3,588,564-location land sample and retain the lower full-sample mean for each configuration. Sort retained members by chronological entry into that fit; preserve selection/swap history in CSVs.',
    f"- Runtime of the full run: **{provenance['elapsed_seconds']:.1f} seconds** ({provenance['elapsed_seconds']/60:.1f} minutes), including full-sample scoring and rendering. Largest distance matrix: **{validation['max_matrix_storage_bytes']/1024**2:.1f} MiB**, not total peak process memory. A full all-candidate/all-land matrix would require about 57 GB before search overhead.",
    f"- **{validation['converged_restart_configurations']} of 32** fitted restart configurations reached training one-swap convergence. **{capped} of the 16** retained trials hit the swap cap. Negative remaining training improvements are recorded; no global optimum is claimed.",
    f"- The largest full-sample mean difference between the two fits of the same configuration was **{max(seed_spreads):.2f} km**; median difference was **{np.median(seed_spreads):.2f} km**. This measures two-seed sensitivity, not a complete uncertainty bound.",
    '- Distance storage is float32 kilometres, with float64 objective reductions; this introduces approximately metre-scale storage precision. Ties use stable station-ID order only. Completeness never enters the score or tie resolution.',
    '- The training subsets approximate the objective. Exact global optimization was not attempted; a converged training fit can remain suboptimal on the full land sample. The 32-swap cap also limits some fits.',
    '- The land mask and NSIDE 1024 sampling are unchanged: Natural Earth land minus lakes, including Antarctica. Fine pixels are about 40.54 km²; tiny islands may have no demand point. Coastline and sampling approximations carry over from the HEALPix report.',
    '- Mean-distance optimization can allocate additional facilities in well-sampled areas when the candidate pool offers no way to improve large empty regions. This is an objective-driven marginal gain, not a quota or compensation for empty cells, and does not establish uniform or climatic representation.',
    '- Prior HEALPix benchmarks were random, not optimized within cells, and have different station counts. Their comparison cannot isolate grid-boundary effects from search quality or budget differences.\n',
    '## Validation\n',
    '- Nine new unit tests cover greedy mean-distance behavior, dense-candidate duplicates, deterministic ties, swap deltas versus brute force, unique counts, objective improvement, swap caps, spherical distances and map-panel marker isolation.',
    f"- Every final network was independently rescored at all {independent['full_land_sample_points']:,} land locations using independently constructed spherical vectors. Maximum discrepancy in the seven requested distance metrics was **{independent['max_independent_metric_error_km']:.3g} km**.",
    '- All selected metadata match the frozen source exactly; IDs are unique and satisfy the applicable completeness threshold. Training sample indices reproduce from their seeds. Each 30-station chosen fit was replayed and reproduced its station IDs.',
    '- All full-sample mean distances exceed their full-candidate lower bounds; mean distance improves with network size in each threshold group. Output hashes and map integrity are checked. Every map panel contains exactly its requested number of station markers.',
    '- Existing eligibility/completeness code and decision/methodology documents are unchanged. No commit or push is part of this experiment.\n',
    '## Files for review\n',
    '- [All 16 metrics](comparison.csv), [both fits](restart-results.csv), [selection trace](selection-trace.csv), [incremental runtime records](performance.csv), and [HEALPix comparison](healpix-comparison.csv).',
    '- [Coverage improvement chart](coverage-improvement.png) (also PDF).',
    '- Maps, each containing all four requested network sizes: [70%](maps/networks-70pct.png), [80%](maps/networks-80pct.png), [85%](maps/networks-85pct.png), [95%](maps/networks-95pct.png) (also PDFs).',
    '- The `networks/` directory contains all 16 selected-station CSVs; [combined selected-station rows](selected-stations-all-networks.csv) are also provided. They are explicitly marked `is_final_network=False`.',
    '- [Numerical validation](validation.json), [independent validation](independent-validation.json), [map validation](map-validation.json), and [provenance](provenance.json).',
    '- Reproducible code, tests, dependency reference and detailed methods: `analysis/facility_location/README.md`.\n'])
    (out/'report.md').write_text('\n'.join(lines).rstrip()+'\n')
    (out/'report-provenance.json').write_text(json.dumps({'report_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'comparison_sha256':hashlib.sha256((out/'comparison.csv').read_bytes()).hexdigest(),
       'report_sha256':hashlib.sha256((out/'report.md').read_bytes()).hexdigest()},indent=2)+'\n')
    # Finalize the bundle manifest after report/validation stages. Keep the
    # numerical-run script identity and timestamp; identify this packaging stage.
    provenance['artifact_manifest_finalized_by_report_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    provenance['output_sha256']={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest()
                               for f in sorted(out.rglob('*')) if f.is_file() and f.name!='provenance.json'}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(out/'report.md')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='data/processed/geography/facility-location');main(p.parse_args().output)
