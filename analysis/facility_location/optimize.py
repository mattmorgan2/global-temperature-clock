#!/usr/bin/env python3
"""Exploratory spherical land-area p-median, without political/grid quotas."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ghcn-facility-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/ghcn-facility-cache')
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import csv
import numpy as np
import healpy as hp
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/healpix'))
from analyze import R,chord_km,vectors,distance_stats

THRESHOLDS=(70,80,85,95)
SIZES=(30,50,75,100)
SEEDS=(2026111301,2026111302)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path,rows):
    rows=list(rows)
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as target:
        w=csv.DictWriter(target,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def make_distances(station_vectors,demand_vectors):
    """Facility x demand, float32 km storage, float64 reductions."""
    out=np.empty((len(station_vectors),len(demand_vectors)),dtype=np.float32)
    for start in range(0,len(station_vectors),128):
        stop=min(start+128,len(station_vectors))
        out[start:stop]=chord_km(cdist(station_vectors[start:stop],demand_vectors)).astype(np.float32)
    return out


def objective(distances,selected):
    return float(np.min(distances[selected],axis=0).mean(dtype=np.float64))


def greedy(distances,count):
    """Exact greedy mean-distance reduction on the supplied discrete demand set."""
    if not 1<=count<=len(distances):raise ValueError('Invalid requested network size')
    selected=[];nearest=np.full(distances.shape[1],np.inf,dtype=np.float32);trace=[]
    for step in range(count):
        costs=np.empty(len(distances),dtype=np.float64)
        for lo in range(0,len(distances),128):
            costs[lo:lo+128]=np.minimum(distances[lo:lo+128],nearest).mean(axis=1,dtype=np.float64)
        costs[selected]=np.inf
        chosen=int(np.argmin(costs))
        selected.append(chosen);nearest=np.minimum(nearest,distances[chosen])
        trace.append(float(nearest.mean(dtype=np.float64)))
    return selected,trace


def best_swap(distances,selected):
    """FastPAM-style exact best single swap for fixed discrete demand distances.

    Addition gain is shared across removal choices. Only points assigned to a
    removed facility need a correction using their second-nearest distance.
    """
    selected=np.asarray(selected,dtype=int)
    if len(selected)<2:raise ValueError('Swap refinement requires at least two facilities')
    chosen=distances[selected]
    owner=np.argmin(chosen,axis=0)
    first=np.min(chosen,axis=0)
    second=np.partition(chosen,1,axis=0)[1]
    excluded=set(map(int,selected))
    best_delta=0.;best_add=best_remove=None
    for candidate in range(len(distances)):
        if candidate in excluded:continue
        with_added=np.minimum(distances[candidate],first)
        base=float(np.sum(with_added-first,dtype=np.float64))
        correction=np.minimum(distances[candidate],second)-with_added
        corrections=np.bincount(owner,weights=correction,minlength=len(selected))
        changes=corrections+base
        removal=int(np.argmin(changes));delta=float(changes[removal])/distances.shape[1]
        if delta<best_delta:
            best_delta,best_add,best_remove=delta,candidate,removal
    return best_add,best_remove,best_delta


def refine(distances,initial,max_swaps=32,tolerance_km=.0001):
    selected=list(initial);entered=list(range(1,len(selected)+1));trace=[]
    before=objective(distances,selected)
    converged=False
    for iteration in range(max_swaps+1):
        addition,slot,delta=best_swap(distances,selected)
        if addition is None or delta>=-tolerance_km:
            converged=True;break
        if iteration==max_swaps:break
        removed=selected[slot]
        proposal=selected.copy();proposal[slot]=addition
        after=objective(distances,proposal)
        if after>before+1e-6:raise AssertionError('A proposed swap increased the objective')
        selected=proposal;entered[slot]=len(initial)+iteration+1
        trace.append({'iteration':iteration+1,'removed_index':removed,'added_index':addition,
                      'slot':slot+1,'training_mean_before_km':before,'training_mean_after_km':after})
        before=after
    return selected,entered,trace,converged,delta


def evaluate(station_vectors,land_vectors):
    nearest=chord_km(cKDTree(station_vectors).query(land_vectors,workers=4)[0])
    nn=chord_km(cKDTree(station_vectors).query(station_vectors,k=2)[0][:,1])
    return nearest,{**distance_stats(nearest,'land_'),**distance_stats(nn,'station_nn_')}


def plot_maps(output,networks,land_pixels,sample_nside):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    output.mkdir(exist_ok=True)
    cmap=plt.get_cmap('YlOrRd').copy();cmap.set_bad('#dcecf6');cmap.set_under('#fffbd5')
    panel_validation=[]
    for threshold in THRESHOLDS:
        figure=plt.figure(figsize=(16,11)); map_axes=[]
        for index,count in enumerate(SIZES,1):
            item=networks[(threshold,count)]
            values=np.load(item['distance_path'])['distances_km']
            sky=np.full(hp.nside2npix(sample_nside),hp.UNSEEN,dtype=np.float64)
            sky[land_pixels]=values
            title=f'≥{threshold}% · {count} stations · mean {item["metrics"]["land_mean_km"]:.0f} km'
            hp.mollview(sky,nest=True,fig=figure.number,sub=(2,2,index),title=title,
                        min=0,max=9000,cmap=cmap,cbar=False,notext=True,xsize=1100,badcolor='#dcecf6',bgcolor='white',flip='geo',margins=(.02,.14,.02,.18))
            stations=item['rows']
            axis=plt.gca();map_axes.append(axis)
            axis.projscatter([float(r['longitude']) for r in stations],[float(r['latitude']) for r in stations],
                           lonlat=True,marker='^',s=24,c='black',edgecolors='white',linewidths=.45,zorder=5)
        marker_counts=[sum(len(c.get_offsets()) for c in axis.collections) for axis in map_axes]
        assert marker_counts==list(SIZES),(threshold,marker_counts)
        panel_validation.append({'threshold_percent':threshold,'expected_station_counts':list(SIZES),'markers_per_panel':marker_counts})
        figure.suptitle('Exploratory land-area p-median · 1976–2025\nBlack triangles: trial stations; land shading: distance to nearest station; blue: ocean/lakes',fontsize=13,y=.985)
        color_ax=figure.add_axes([.22,.035,.56,.02])
        figure.colorbar(ScalarMappable(norm=Normalize(0,9000),cmap=cmap),cax=color_ax,orientation='horizontal',label='Great-circle distance to nearest selected station (km)')
        figure.savefig(output/f'networks-{threshold}pct.png',dpi=160,facecolor='white')
        figure.savefig(output/f'networks-{threshold}pct.pdf',dpi=160,facecolor='white')
        plt.close(figure)
    (output.parent/'map-validation.json').write_text(json.dumps(panel_validation,indent=2)+'\n')


def plot_improvement(output,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,2,figsize=(13,5))
    for threshold in THRESHOLDS:
        chosen=[r for r in summary if r['threshold_percent']==threshold]
        axes[0].plot([r['network_size'] for r in chosen],[r['land_mean_km'] for r in chosen],marker='o',label=f'≥{threshold}%')
        axes[1].plot([r['network_size'] for r in chosen],[r['land_p95_km'] for r in chosen],marker='o',label=f'≥{threshold}%')
        axes[0].axhline(chosen[0]['full_candidate_pool_mean_lower_bound_km'],alpha=.25,linestyle='--',color=axes[0].lines[-1].get_color())
    for ax in axes:
        ax.set_xlabel('Trial network size');ax.set_xticks(SIZES);ax.set_ylabel('Land-to-nearest-station distance (km)');ax.grid(alpha=.2);ax.legend()
    axes[0].set_title('Mean distance: optimization objective\nDashed: full-candidate-pool lower bounds')
    axes[1].set_title('95th percentile: evaluated, not optimized')
    figure.suptitle('Exploratory geographic coverage; equal land-area weights including Antarctica')
    figure.tight_layout();figure.savefig(output/'coverage-improvement.png',dpi=180);figure.savefig(output/'coverage-improvement.pdf');plt.close(figure)


def run(args):
    started=time.perf_counter();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    for name in ('networks','maps'): (out/name).mkdir(exist_ok=True)
    cache=Path(args.cache);cache.mkdir(parents=True,exist_ok=True)
    input_path=Path(args.stations)
    all_rows=sorted(csv.DictReader(input_path.open()),key=lambda r:r['station_id'])
    if len({r['station_id'] for r in all_rows})!=len(all_rows):raise ValueError('Duplicate station ID')
    if any(int(r['total_calendar_days'])!=18263 for r in all_rows):raise ValueError('Expected 1976–2025 completeness input')
    data=np.load(args.land_sample)
    pixels=data['pixels'];sample_nside=int(data['nside']);comparison_ids=data['simulation_indices']
    lon,lat=hp.pix2ang(sample_nside,pixels,nest=True,lonlat=True);land_vectors=vectors(lon,lat)
    sample_indices=[]
    for seed in SEEDS:
        sample_indices.append(np.random.default_rng(seed).choice(len(pixels),args.training_points,replace=False))
    np.savez_compressed(out/'optimization-demand-samples.npz',seeds=np.array(SEEDS),indices=np.stack(sample_indices))
    land_baseline={int(r['threshold_percent']):r for r in csv.DictReader(Path(args.healpix_results,'land-nearest-station-distances.csv').open())}
    baseline_simulations=list(csv.DictReader(Path(args.healpix_results,'one-per-cell-simulations.csv').open()))
    summary=[];restart_rows=[];traces=[];networks={};performance=[]
    for threshold in THRESHOLDS:
        candidate_rows=[r for r in all_rows if int(r['both_valid_days'])*100>=18263*threshold]
        sv=vectors([float(r['longitude']) for r in candidate_rows],[float(r['latitude']) for r in candidate_rows])
        expected={70:3992,80:3725,85:3476,95:2202}[threshold]
        if len(candidate_rows)!=expected:raise ValueError('Candidate pool mismatch')
        for restart,(seed,indices) in enumerate(zip(SEEDS,sample_indices)):
            begin=time.perf_counter()
            print(f'Fit threshold {threshold}%, restart {restart+1}, {len(candidate_rows)} candidates / {len(indices)} land points',flush=True)
            distances=make_distances(sv,land_vectors[indices]);prefix,costs=greedy(distances,max(SIZES))
            for step,(station,cost) in enumerate(zip(prefix,costs),1):
                traces.append({'threshold_percent':threshold,'restart':restart+1,'network_size':0,'action':'greedy_add','step':step,'station_id':candidate_rows[station]['station_id'],'removed_station_id':'','training_mean_km':cost})
            for count in SIZES:
                t=time.perf_counter()
                selected,entered,swaps,converged,remaining=refine(distances,prefix[:count],args.max_swaps)
                order=np.argsort(entered,kind='stable')
                selected=[selected[i] for i in order];entered=[entered[i] for i in order]
                nearest,metrics=evaluate(sv[selected],land_vectors)
                record={'threshold_percent':threshold,'network_size':count,'restart':restart+1,'seed':seed,
                        'candidate_count':len(candidate_rows),'training_points':len(indices),'swaps':len(swaps),
                        'one_swap_converged':converged,'best_remaining_swap_training_delta_km':remaining,
                        'training_mean_km':objective(distances,selected),**metrics}
                restart_rows.append(record)
                for s in swaps:
                    traces.append({'threshold_percent':threshold,'restart':restart+1,'network_size':count,'action':'swap','step':count+s['iteration'],'station_id':candidate_rows[s['added_index']]['station_id'],'removed_station_id':candidate_rows[s['removed_index']]['station_id'],'training_mean_km':s['training_mean_after_km']})
                key=(threshold,count)
                if key not in networks or metrics['land_mean_km']<networks[key]['metrics']['land_mean_km']:
                    chosen=[]
                    for rank,(i,step) in enumerate(zip(selected,entered),1):
                        chosen.append({**candidate_rows[i],'selection_order':rank,'entered_at_algorithm_step':int(step),
                                       'trial_threshold_percent':threshold,'trial_network_size':count,'restart':restart+1,'seed':seed,'is_final_network':False})
                    distance_path=cache/f'land-distances-{threshold}pct-{count}.npz'
                    np.savez_compressed(distance_path,distances_km=nearest.astype(np.float32))
                    networks[key]={'rows':chosen,'metrics':metrics,'record':record,'distance_path':distance_path,
                                   'comparison_metrics':distance_stats(nearest[comparison_ids],'comparison_land_')}
                performance.append({'threshold_percent':threshold,'restart':restart+1,'network_size':count,'seconds_refine_and_evaluate':time.perf_counter()-t})
                print(f'  n={count}: full mean {metrics["land_mean_km"]:.2f} km, {len(swaps)} swaps, converged={converged}',flush=True)
            del distances
            print(f'  restart elapsed {time.perf_counter()-begin:.1f}s',flush=True)
    comparisons=[]
    for threshold in THRESHOLDS:
        previous=None
        for count in SIZES:
            item=networks[(threshold,count)];record=item['record'];metrics=item['metrics']
            row={**record,'restart':record['restart'],**item['comparison_metrics'],
                 'full_candidate_pool_mean_lower_bound_km':float(land_baseline[threshold]['mean_km']),
                 'mean_above_full_pool_km':metrics['land_mean_km']-float(land_baseline[threshold]['mean_km']),
                 'mean_improvement_from_previous_size_km':None if previous is None else previous['land_mean_km']-metrics['land_mean_km'],
                 'mean_improvement_from_previous_size_percent':None if previous is None else 100*(previous['land_mean_km']-metrics['land_mean_km'])/previous['land_mean_km'],
                 'added_stations':None if previous is None else count-previous['network_size']}
            summary.append(row);previous=row
            chosen=item['rows']
            assert len(chosen)==count and len({r['station_id'] for r in chosen})==count
            assert all(int(r['both_valid_days'])*100>=18263*threshold for r in chosen)
            assert metrics['land_mean_km']>=float(land_baseline[threshold]['mean_km'])-1e-6
            write_csv(out/'networks'/f'network-{threshold}pct-{count}.csv',chosen)
            base=[r for r in baseline_simulations if int(r['threshold_percent'])==threshold and abs(int(r['network_size'])-count)/count<=.20]
            for n in sorted({int(r['global_cells']) for r in base}):
                selected=[r for r in base if int(r['global_cells'])==n]
                comparisons.append({'threshold_percent':threshold,'optimized_network_size':count,'healpix_global_cells':n,'healpix_network_size':int(selected[0]['network_size']),
                    'size_difference_percent':100*(int(selected[0]['network_size'])-count)/count,'random_network_count':len(selected),
                    'optimized_mean_same_sample_km':item['comparison_metrics']['comparison_land_mean_km'],
                    'random_mean_median_km':float(np.median([float(r['land_nearest_mean_km']) for r in selected])),
                    'optimized_p95_same_sample_km':item['comparison_metrics']['comparison_land_p95_km'],
                    'random_p95_median_km':float(np.median([float(r['land_nearest_p95_km']) for r in selected]))})
    write_csv(out/'comparison.csv',summary);write_csv(out/'restart-results.csv',restart_rows)
    write_csv(out/'selection-trace.csv',traces);write_csv(out/'performance.csv',performance)
    write_csv(out/'healpix-comparison.csv',comparisons)
    print('Rendering maps and improvement chart',flush=True)
    if args.maps:plot_maps(out/'maps',networks,pixels,sample_nside)
    plot_improvement(out,summary)
    validation={'all_networks_have_requested_unique_eligible_station_count':True,'all_full_sample_means_above_full_pool_lower_bound':True,
      'converged_restart_configurations':sum(r['one_swap_converged'] for r in restart_rows),'total_restart_configurations':len(restart_rows),
      'mean_monotone_with_network_size':all(a['land_mean_km']>=b['land_mean_km']-1e-8 for t in THRESHOLDS for a,b in zip([r for r in summary if r['threshold_percent']==t],[r for r in summary if r['threshold_percent']==t][1:])),
      'land_sample_points':len(pixels),'training_points_per_restart':args.training_points,
      'max_matrix_storage_bytes':max({70:3992,80:3725,85:3476,95:2202}.values())*args.training_points*4}
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    provenance={'generated_at':datetime.now(timezone.utc).isoformat(),'analysis_script_sha256':sha256(__file__),'git_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
      'station_metrics_sha256':sha256(args.stations),'land_sample_sha256':sha256(args.land_sample),
      'healpix_provenance_sha256':sha256(Path(args.healpix_results,'provenance.json')),
      'period':['1976-01-01','2025-12-31'],'thresholds':THRESHOLDS,'network_sizes':SIZES,'seeds':SEEDS,
      'training_points':args.training_points,'max_swaps':args.max_swaps,'swap_tolerance_mean_km':.0001,
      'earth_radius_km':R,'optimization_distance_storage':'float32 km; float64 objective sums',
      'tie_break':'ascending station ID; completeness never used in geographic score or ties',
      'restart_choice':'lowest mean distance on the full existing land sample',
      'elapsed_seconds':time.perf_counter()-started,
      'dependencies':{p:importlib.metadata.version(p) for p in ('numpy','scipy','healpy','matplotlib')},
      'output_sha256':{str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file() and p.name!='provenance.json'}}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'comparison':summary,'validation':validation},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stations',default='data/processed/geography/inputs/completeness-1976-2025.csv')
    p.add_argument('--land-sample',default='data/processed/geography/healpix/land-distance-sample.npz')
    p.add_argument('--healpix-results',default='data/processed/geography/healpix')
    p.add_argument('--output',default='data/processed/geography/facility-location')
    p.add_argument('--cache',default='data/raw/geography/facility-location')
    p.add_argument('--training-points',type=int,default=16384)
    p.add_argument('--max-swaps',type=int,default=32)
    p.add_argument('--maps',action=argparse.BooleanOptionalAction,default=True)
    run(p.parse_args())
