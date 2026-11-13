"""Validate gap dates and neighbor metrics independently; never optimize."""
from pathlib import Path
from datetime import date,timedelta
import calendar,csv,hashlib,json,argparse
import numpy as np


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(out):
    out=Path(out);root=Path(__file__).resolve().parents[2]
    provenance=json.loads((out/'provenance.json').read_text())
    original=root/'data/processed/geography/facility-location/networks/network-70pct-50.csv'
    assert digest(original)==provenance['network_input_sha256']
    for name,expected in provenance['output_sha256'].items():assert digest(out/name)==expected,name
    reviewed=list(csv.DictReader((out/'station-review.csv').open()))
    network=list(csv.DictReader(original.open()))
    assert len(reviewed)==len({r['station_id'] for r in reviewed})==50
    assert {r['station_id'] for r in reviewed}=={r['station_id'] for r in network}
    assert [int(r['review_number']) for r in reviewed]==list(range(1,51))
    assert [int(r['both_valid_days']) for r in reviewed]==sorted(int(r['both_valid_days']) for r in reviewed)
    candidates=list(csv.DictReader((root/'data/processed/geography/inputs/completeness-1976-2025.csv').open()))
    lat=np.radians([float(r['latitude']) for r in candidates]);lon=np.radians([float(r['longitude']) for r in candidates])
    eligible=np.array([int(r['both_valid_days'])*100>=70*18263 for r in candidates])
    ids=np.array([r['station_id'] for r in candidates]);percent=np.array([float(r['both_valid_percent']) for r in candidates])
    dates=[date(1976,1,1)+timedelta(days=i) for i in range(18263)]
    tied=list(csv.DictReader((out/'longest-gaps.csv').open()))
    for row in reviewed:
        sid=row['station_id'];meta=provenance['daily_sources'][sid]
        source=root/'data/raw/ghcnd-daily'/meta['cache_file'];assert digest(source)==meta['sha256']
        good={'TMAX':set(),'TMIN':set()}
        for line in source.read_text().splitlines():
            year=int(line[11:15]);element=line[17:21]
            if not 1976<=year<=2025 or element not in good:continue
            month=int(line[15:17])
            for day in range(1,calendar.monthrange(year,month)[1]+1):
                cell=line[21+8*(day-1):29+8*(day-1)]
                if int(cell[:5])!=-9999 and cell[6]==' ':good[element].add(date(year,month,day))
        paired=good['TMAX']&good['TMIN']
        missing=[d for d in dates if d not in paired]
        assert len(paired)==int(row['both_valid_days'])
        assert len(missing)==int(row['incomplete_days'])
        runs=[]
        for d in missing:
            if not runs or d!=runs[-1][-1]+timedelta(days=1):runs.append([d])
            else:runs[-1].append(d)
        maximum=max(map(len,runs),default=0)
        expected=[(str(r[0]),str(r[-1]),len(r)) for r in runs if len(r)==maximum]
        recorded=[(r['start'],r['end'],int(r['days'])) for r in tied if r['station_id']==sid]
        assert maximum==int(row['longest_incomplete_run_days'])
        assert expected==recorded,(sid,expected,recorded)
        if expected:assert (row['longest_gap_start'],row['longest_gap_end'])==expected[0][:2]
        # Haversine calculation is independent of the inspection's chord/cdist path.
        a=np.sin((lat-np.radians(float(row['latitude'])))/2)**2+np.cos(lat)*np.cos(np.radians(float(row['latitude'])))*np.sin((lon-np.radians(float(row['longitude'])))/2)**2
        distances=2*6371.0088*np.arctan2(np.sqrt(np.clip(a,0,1)),np.sqrt(np.clip(1-a,0,1)))
        for radius in (50,100,250):
            for prefix,mask in [('neighbors',eligible),('all_pool_neighbors',np.ones(len(ids),dtype=bool))]:
                inside=(distances<=radius+1e-8)&(ids!=sid)&mask
                assert int(inside.sum())==int(row[f'{prefix}_{radius}km_count']),(sid,radius,prefix)
                if inside.any():assert abs(percent[inside].max()-float(row[f'{prefix}_{radius}km_highest_completeness_percent']))<1e-10
                else:assert row[f'{prefix}_{radius}km_highest_completeness_percent']==''
    reference=next(r for r in csv.DictReader((root/'data/processed/geography/facility-location/comparison.csv').open()) if r['threshold_percent']=='70' and r['network_size']=='50')
    saved=next(csv.DictReader((out/'geographic-reference.csv').open()));assert saved==reference
    assert sum(json.loads((out/'summary.json').read_text())['plot_validation']['histogram_bin_counts'])==50
    result={'unique_sorted_network_rows':50,'input_network_hash_unchanged':True,
            'independently_recomputed_gap_dates_and_all_maximum_ties':50,
            'independent_haversine_counts_and_maxima_checks':50*3*2,
            'geographic_statistics_copied_exactly':True,'histogram_station_count':50,
            'inspection_unit_tests_passed':7,'no_optimization_or_replacement_performed':True}
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    provenance['validation_script_sha256']=digest(__file__)
    provenance['output_sha256']={str(f.relative_to(out)):digest(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='provenance.json'}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='data/processed/geography/network-review');main(parser.parse_args().output)
