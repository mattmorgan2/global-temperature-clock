"""Independently rescore every trial network and replay each 30-station fit."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys
import numpy as np
from scipy.spatial import cKDTree
from optimize import R,SEEDS,THRESHOLDS,greedy,refine,make_distances,vectors
import healpy as hp


def independent_metrics(lon,lat,land_vectors):
    lon,lat=np.radians(lon),np.radians(lat)
    vv=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    nearest=cKDTree(vv).query(land_vectors,workers=4)[0]
    nearest=2*R*np.arcsin(np.clip(nearest/2,0,1))
    nn=cKDTree(vv).query(vv,k=2,workers=4)[0][:,1]
    nn=2*R*np.arcsin(np.clip(nn/2,0,1))
    return {'land_mean_km':float(nearest.mean()),'land_p50_km':float(np.percentile(nearest,50)),
            'land_p90_km':float(np.percentile(nearest,90)),'land_p95_km':float(np.percentile(nearest,95)),
            'station_nn_min_km':float(nn.min()),'station_nn_p50_km':float(np.percentile(nn,50)),
            'station_nn_p90_km':float(np.percentile(nn,90))}


def main(args):
    out=Path(args.output)
    data=np.load(args.land_sample);pixels=data['pixels'];nside=int(data['nside'])
    lon,lat=hp.pix2ang(nside,pixels,nest=True,lonlat=True)
    lon,lat=np.radians(lon),np.radians(lat)
    land=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    summary=list(csv.DictReader((out/'comparison.csv').open()))
    if len(summary)!=16:raise AssertionError('Expected all 16 configurations')
    source=sorted(csv.DictReader(Path(args.stations).open()),key=lambda r:r['station_id'])
    source_by_id={r['station_id']:r for r in source}
    samples=np.load(out/'optimization-demand-samples.npz')
    indices=samples['indices'];provenance=json.loads((out/'provenance.json').read_text())
    for seed,ids in zip(SEEDS,indices):
        assert len(set(ids))==provenance['training_points']
        np.testing.assert_array_equal(ids,np.random.default_rng(seed).choice(len(pixels),len(ids),replace=False))
    max_error=0.;replayed=[]
    for record in summary:
        threshold,count=int(record['threshold_percent']),int(record['network_size'])
        rows=list(csv.DictReader((out/'networks'/f'network-{threshold}pct-{count}.csv').open()))
        assert len(rows)==len({r['station_id'] for r in rows})==count
        assert [int(r['selection_order']) for r in rows]==list(range(1,count+1))
        assert [int(r['entered_at_algorithm_step']) for r in rows]==sorted(int(r['entered_at_algorithm_step']) for r in rows)
        for r in rows:
            assert r['is_final_network']=='False'
            assert int(r['both_valid_days'])*100>=18263*threshold
            assert all(r[k]==value for k,value in source_by_id[r['station_id']].items())
        metrics=independent_metrics(np.array([float(r['longitude']) for r in rows]),np.array([float(r['latitude']) for r in rows]),land)
        for key,value in metrics.items():
            error=abs(value-float(record[key]));max_error=max(max_error,error)
            assert error<1e-6,(threshold,count,key,error)
        if count==30 and args.replay:
            candidates=[r for r in source if int(r['both_valid_days'])*100>=18263*threshold]
            sv=vectors([float(r['longitude']) for r in candidates],[float(r['latitude']) for r in candidates])
            restart=int(record['restart'])-1
            train_lon,train_lat=hp.pix2ang(nside,pixels[indices[restart]],nest=True,lonlat=True)
            distances=make_distances(sv,vectors(train_lon,train_lat))
            prefix,_=greedy(distances,30)
            selected,entered,_,_,_=refine(distances,prefix,provenance['max_swaps'])
            order=np.argsort(entered,kind='stable')
            # Reconstructed unit vectors may differ at roundoff scale; tolerance
            # is for geographic statistics, while deterministic IDs must match.
            assert [candidates[selected[i]]['station_id'] for i in order]==[r['station_id'] for r in rows]
            replayed.append({'threshold_percent':threshold,'network_size':count,'restart':restart+1})
        print(f'Validated threshold {threshold}%, n={count}',flush=True)
    map_panels=json.loads((out/'map-validation.json').read_text())
    assert len(map_panels)==4
    assert all(r['markers_per_panel']==[30,50,75,100] for r in map_panels)
    for relative,digest in provenance['output_sha256'].items():
        assert hashlib.sha256((out/relative).read_bytes()).hexdigest()==digest,relative
    result={'network_count':16,'full_land_sample_points':len(pixels),'max_independent_metric_error_km':max_error,
            'all_selected_rows_preserve_input_metadata':True,'all_requested_counts_unique_and_eligible':True,
            'all_training_sample_indices_reproduce_from_seeds':True,'replayed_30_station_networks':replayed,
            'all_original_output_hashes_match':True,'all_16_map_panel_marker_counts_match_network_sizes':True}
    (out/'independent-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='data/processed/geography/facility-location')
    p.add_argument('--stations',default='data/processed/geography/inputs/completeness-1976-2025.csv')
    p.add_argument('--land-sample',default='data/processed/geography/healpix/land-distance-sample.npz')
    p.add_argument('--replay',action=argparse.BooleanOptionalAction,default=True)
    main(p.parse_args())
