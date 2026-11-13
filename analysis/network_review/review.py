#!/usr/bin/env python3
"""Inspect a frozen station network; no selection, optimization or infilling."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ghcn-network-review-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/ghcn-network-review-cache')
from collections import Counter
from datetime import date,timedelta,datetime,timezone
import argparse,csv,hashlib,json,sys
from pathlib import Path
import numpy as np
import healpy as hp
from scipy.spatial.distance import cdist

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'data-pipeline/src'))
sys.path.insert(0,str(ROOT/'analysis/healpix'))
from temperature_pipeline.completeness import parse_daily,analyze_daily
from analyze import vectors,chord_km
START=date(1976,1,1);END=date(2025,12,31);DAYS=(END-START).days+1
RADII=(50,100,250)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path,rows):
    rows=list(rows)
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def incomplete_runs(valid,start):
    runs=[];begin=None
    for i,complete in enumerate(valid):
        if not complete and begin is None:begin=i
        elif complete and begin is not None:
            runs.append({'start':str(start+timedelta(days=begin)),'end':str(start+timedelta(days=i-1)),'days':i-begin});begin=None
    if begin is not None:runs.append({'start':str(start+timedelta(days=begin)),'end':str(start+timedelta(days=len(valid)-1)),'days':len(valid)-begin})
    return runs


def inspect_daily(path,station_id,start=START,end=END):
    total=(end-start).days+1
    valid=np.zeros((total,2),dtype=bool)
    observed={element:[] for element in ('TMAX','TMIN')}
    accepted={element:[] for element in observed}
    rejected=Counter();seen=set()
    with Path(path).open(encoding='ascii') as source:
        for number,line in enumerate(source,1):
            if len(line.rstrip('\r\n'))!=269 or line[:11]!=station_id:
                raise ValueError(f'{path}:{number}: malformed record or station mismatch')
            if line[17:21] not in observed:continue
            _,year,month,element,cells=parse_daily(line,station_id)
            key=(year,month,element)
            if key in seen:raise ValueError(f'Duplicate element month: {key}')
            seen.add(key)
            column=0 if element=='TMAX' else 1
            for day,(value,mflag,qflag,sflag) in enumerate(cells,1):
                d=date(year,month,day)
                if value!=-9999:
                    observed[element].append(year)
                    if qflag==' ':accepted[element].append(year)
                if not start<=d<=end:continue
                offset=(d-start).days
                if value!=-9999 and qflag==' ':valid[offset,column]=True
                elif value!=-9999:rejected[element]+=1
    paired=valid.all(axis=1)
    runs=incomplete_runs(paired,start)
    maximum=max((r['days'] for r in runs),default=0)
    longest=[r for r in runs if r['days']==maximum]
    result={'total_calendar_days':total,'valid_tmax_days':int(valid[:,0].sum()),'valid_tmin_days':int(valid[:,1].sum()),
      'both_valid_days':int(paired.sum()),'both_valid_percent':100*int(paired.sum())/total,'incomplete_days':int((~paired).sum()),
      'longest_incomplete_run_days':maximum,'longest_gap_start':longest[0]['start'] if longest else '',
      'longest_gap_end':longest[0]['end'] if longest else '', 'longest_gap_tied_run_count':len(longest),
      'incomplete_run_count':len(runs),'qc_rejected_tmax_days':rejected['TMAX'],'qc_rejected_tmin_days':rejected['TMIN']}
    for element in observed:
        for tag,values in [('observed',observed[element]),('valid',accepted[element])]:
            result[f'{element.lower()}_first_{tag}_year']=min(values) if values else ''
            result[f'{element.lower()}_last_{tag}_year']=max(values) if values else ''
    return result,runs,longest


def neighbors(station,candidates,distances):
    rows=[]
    for candidate,distance in zip(candidates,distances):
        if candidate['station_id']==station['station_id'] or distance>250+1e-8:continue
        rows.append({'candidate_station_id':candidate['station_id'],'candidate_station_name':candidate['station_name'],
          'candidate_country':candidate['country_name'],'candidate_latitude':candidate['latitude'],'candidate_longitude':candidate['longitude'],
          'distance_km':float(distance),'candidate_both_valid_days':int(candidate['both_valid_days']),
          'candidate_completeness_percent':float(candidate['both_valid_percent']),
          'candidate_eligible_70pct':int(candidate['both_valid_days'])*100>=int(candidate['total_calendar_days'])*70,
          'completeness_gain_percentage_points':float(candidate['both_valid_percent'])-float(station['both_valid_percent'])})
    return sorted(rows,key=lambda r:(r['distance_km'],r['candidate_station_id']))


def radius_summary(nearby,radius,eligible_only=True):
    chosen=[r for r in nearby if r['distance_km']<=radius+1e-8 and (r['candidate_eligible_70pct'] or not eligible_only)]
    if not chosen:return {'count':0,'highest_completeness_percent':'','highest_completeness_station_id':'','highest_completeness_station_name':'','highest_completeness_station_distance_km':''}
    best=min(chosen,key=lambda r:(-r['candidate_both_valid_days'],r['distance_km'],r['candidate_station_id']))
    return {'count':len(chosen),'highest_completeness_percent':best['candidate_completeness_percent'],
      'highest_completeness_station_id':best['candidate_station_id'],'highest_completeness_station_name':best['candidate_station_name'],
      'highest_completeness_station_distance_km':best['distance_km']}


def substantial(station,nearby,min_gain=5):
    return [r for r in nearby if r['distance_km']<=100+1e-8 and r['candidate_eligible_70pct'] and
            (r['candidate_both_valid_days']-int(station['both_valid_days']))*100>=min_gain*int(station['total_calendar_days'])]


def make_plots(out,rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    source=np.load(ROOT/'data/processed/geography/healpix/land-distance-sample.npz')
    sky=np.full(hp.nside2npix(int(source['nside'])),hp.UNSEEN,dtype=np.float64);sky[source['pixels']]=1
    fig=plt.figure(figsize=(17,10))
    hp.mollview(sky,nest=True,fig=fig.number,flip='geo',cmap=ListedColormap(['#e2e5df']),min=0,max=1,cbar=False,notext=True,
                badcolor='#dcecf6',bgcolor='white',title='Fixed 70% / 50-station trial network · numbers match ascending-completeness table',xsize=2200,margins=(.02,.09,.02,.12))
    ax=plt.gca()
    ax.projscatter([float(r['longitude']) for r in rows],[float(r['latitude']) for r in rows],lonlat=True,s=24,c='#a71930',edgecolors='white',linewidths=.5)
    for row in rows:
        x,y=ax.proj.ang2xy(float(row['longitude']),float(row['latitude']),lonlat=True)
        ax.annotate(str(row['review_number']),(x,y),xytext=(4,3),textcoords='offset points',fontsize=8,fontweight='bold',
                    bbox={'facecolor':'white','edgecolor':'none','alpha':.8,'pad':.7})
    assert sum(len(c.get_offsets()) for c in ax.collections)==50
    assert len(ax.texts)==50,(len(ax.texts))
    fig.text(.5,.08,'1976–2025 paired TMAX/TMIN completeness · no stations changed · land mask: existing Natural Earth / HEALPix sample',ha='center',fontsize=10)
    fig.savefig(out/'numbered-network-map.png',dpi=180);fig.savefig(out/'numbered-network-map.pdf',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    values=[float(r['both_valid_percent']) for r in rows]
    counts,edges,_=ax.hist(values,bins=np.arange(70,105,5),edgecolor='white',color='#286c83')
    for count,left,right in zip(counts,edges[:-1],edges[1:]):
        ax.text((left+right)/2,count+.12,str(int(count)),ha='center')
    ax.set(xlabel='Historical paired-valid completeness, 1976–2025 (%)',ylabel='Selected station count',title='Completeness of the existing 50-station network',xticks=np.arange(70,101,5))
    ax.grid(axis='y',alpha=.2);ax.set_ylim(0,max(counts)+2);fig.tight_layout()
    fig.savefig(out/'completeness-histogram.png',dpi=180);fig.savefig(out/'completeness-histogram.pdf');plt.close(fig)
    return {'map_markers':50,'map_number_labels':50,'histogram_bin_counts':counts.astype(int).tolist(),'histogram_edges_percent':edges.tolist()}


def report(out,rows,summary,flags,coverage):
    lines=['# Inspection of the saved 70% / 50-station network\n',
    '**Inspection only:** the selected network, geographic optimization, eligibility and completeness methodology are unchanged. No replacement is proposed. Every day in 1976–2025 is weighted equally; no recent/historical weighting or missing-day fill is applied.\n',
    '## Definitions and source availability\n',
    '- Review numbers follow ascending full-precision historical completeness, then station ID; these are the numbers on the map. Original optimization selection order is retained in the CSV.',
    '- Primary nearby counts/highest completeness use the **3,992 candidates eligible at 70%** from the frozen 1976–2025 analysis, excluding the station itself. Other selected stations would count if within range; the network’s minimum separation is about 916 km, so none are within 250 km. Secondary columns also report the full 5,243 pre-threshold candidate pool.',
    '- Distances are inclusive great-circle radii on the same 6,371.0088-km sphere as the geographic analysis. Nearby station IDs are not merged even if coordinates coincide. No political borders restrict the search.',
    '- A complete day requires recorded TMAX and TMIN, neither missing (`-9999`), each with blank QFLAG. Missing months/elements count as incomplete. Longest-gap dates are inclusive and restricted to 1976-01-01 through 2025-12-31. If equal-length maxima occur, the main table displays the earliest; every tied maximum is in longest-gaps.csv.',
    '- Observed first/last years below are derived from any nonmissing element values in the entire cached `.dly` file, including outside 1976–2025 and values carrying QC flags. The CSV separately preserves original inventory endpoint years and QC-valid first/last years. Endpoints do not prove continuity.',
    f"- All **{summary['available_daily_files']}/50** canonical cached source files were available and matched their original source-provenance hashes; no fresh downloads were made. Unknown elevations: **{summary['unknown_elevations']}**. Inventory-versus-file endpoint mismatches: **{summary['endpoint_mismatch_stations']}** stations (details in endpoint-checks.csv). A blank nearby maximum means no other candidate in that radius, not 0% completeness.",
    '- No substitution is applied in this inspection. The provisional rule is the arithmetic mean of the ten most recent valid same-month/day observations from the same station in preceding years; see the [decision log](../../../../docs/decisions.md#provisional-same-calendar-date-substitution). Preceding calendar days, substituted values and future years are not used. Station moves, source equivalence, climatic representativeness and replacement coverage effects are not evaluated.\n',
    '## Complete station table\n',
    'Nearby entries are **other-candidate count / highest historical completeness**. All percentages describe paired-valid days over the same 18,263-day window. Elevation is metres; coordinates are degrees.\n',
    '| No. | ID / station | Country | Latitude, longitude | Elevation | Complete | Incomplete days | Longest gap: days; start → end | TMAX observed years | TMIN observed years | Within 50 km | Within 100 km | Within 250 km |\n|---:|---|---|---|---:|---:|---:|---|---|---|---:|---:|---:|']
    for r in rows:
        peers=[]
        for radius in RADII:
            n=r[f'neighbors_{radius}km_count'];best=r[f'neighbors_{radius}km_highest_completeness_percent']
            peers.append(f'{n} / '+(f'{best:.2f}%' if best!='' else '—'))
        gap=f"{r['longest_incomplete_run_days']}; {r['longest_gap_start']} → {r['longest_gap_end']}" if r['longest_incomplete_run_days'] else '0; none'
        lines.append(f"| {r['review_number']} | {r['station_id']} / {r['station_name']} | {r['country_name']} | {float(r['latitude']):.4f}, {float(r['longitude']):.4f} | {r['elevation'] or 'unknown'} | {float(r['both_valid_percent']):.2f}% | {r['incomplete_days']} | {gap} | {r['tmax_first_observed_year']}–{r['tmax_last_observed_year']} | {r['tmin_first_observed_year']}–{r['tmin_last_observed_year']} | "+' | '.join(peers)+' |')
    lines.extend(['\n[Full CSV with separate fields, inventory/QC-valid endpoints and both neighbor pools](station-review.csv). [Numbered map](numbered-network-map.png). [Completeness histogram](completeness-histogram.png).\n',
    '## Longest incomplete gaps\n',
    f"Historical completeness ranges from **{summary['minimum_completeness_percent']:.2f}%** to **{summary['maximum_completeness_percent']:.2f}%**, median **{summary['median_completeness_percent']:.2f}%**. **{summary['stations_with_gap_at_least_365_days']}** stations have a longest gap of at least 365 days; **{summary['stations_with_gap_at_least_730_days']}** have one of at least 730 days. These are absent/invalid paired days, not necessarily total station outages.\n",
    '| No. | Station | Longest gap | Inclusive start | Inclusive end |\n|---:|---|---:|---|---|'])
    for r in sorted(rows,key=lambda r:(-r['longest_incomplete_run_days'],r['station_id']))[:15]:
        lines.append(f"| {r['review_number']} | {r['station_id']} / {r['station_name']} | {r['longest_incomplete_run_days']} days | {r['longest_gap_start']} | {r['longest_gap_end']} |")
    lines.extend(['\n[All longest gaps, including ties](longest-gaps.csv); [every incomplete run](incomplete-runs.csv).\n',
    '## Nearby substantially more complete observations\n',
    '**Inspection flag:** another 70%-eligible candidate within 100 km has at least **5 percentage points** higher historical paired completeness. This is a descriptive flag, not a new eligibility rule or a proposed replacement. Completeness gains use exact day counts before display rounding. Every flagged candidate is listed in the companion CSV. No geographic optimization, replacement coverage calculation, climate equivalence test or site-history assessment has been performed.\n',
    '| No. | Selected station | Selected completeness | Highest-completeness nearby candidate | Distance | Nearby completeness | Gain | Number meeting flag |\n|---:|---|---:|---|---:|---:|---:|---:|'])
    for r in flags:
        lines.append(f"| {r['review_number']} | {r['station_id']} / {r['station_name']} | {r['selected_completeness_percent']:.2f}% | {r['candidate_station_id']} / {r['candidate_station_name']} | {r['distance_km']:.1f} km | {r['candidate_completeness_percent']:.2f}% | {r['completeness_gain_percentage_points']:.2f} pp | {r['substantially_more_complete_candidates_within_100km']} |")
    if not flags:lines.append('| — | None meet this inspection flag | — | — | — | — | — | — |')
    lines.extend([f"\n**{len(flags)} of 50 selected stations** meet the inspection flag. [Flagged stations](stations-with-nearby-higher-completeness.csv); [all qualifying nearby differences](substantially-more-complete-neighbors-within-100km.csv); [all candidate neighbors within 250 km](nearby-candidates.csv).\n",
    '## Existing geographic coverage, for reference\n',
    'Copied from the committed facility-location comparison row; no new geographic selection or optimization was run. Land statistics use all 3,588,564 equal-area locations, including Antarctica. NN is the distance to each selected station’s nearest other selected station.\n',
    '| Metric | Distance |\n|---|---:|'])
    for label,key in [('Mean land-to-nearest station','land_mean_km'),('Median land distance','land_p50_km'),('Land distance p90','land_p90_km'),('Land distance p95','land_p95_km'),('Minimum selected-station NN distance','station_nn_min_km'),('Median selected-station NN distance','station_nn_p50_km'),('Selected-station NN distance p90','station_nn_p90_km')]:
        lines.append(f'| {label} | {float(coverage[key]):,.2f} km |')
    lines.extend(['\n[Original geographic statistics row](geographic-reference.csv). The original trial is exploratory, not a final adopted network.\n',
    '## Validation and reproducibility\n',
    'The selected input and frozen candidate CSVs are hash-checked, all daily files are checked against the original per-station provenance, and daily paired counts/longest lengths reconcile exactly with the saved metrics and the existing daily-analysis function. Neighbor counts reconcile across radii and candidate pools; maxima exclude self and the 5-pp flags are checked with integer day counts. Map numbers correspond to exactly 50 unique rows. No missing values are silently filled. Validation and source/output hashes are saved with this report.\n',
    'Read-only inspection code and tests: `analysis/network_review/`. Original input network: `data/processed/geography/facility-location/networks/network-70pct-50.csv`. Source metadata are frozen as of the saved November 2026 run; dates and coordinates are not a history of station moves.\n'])
    (out/'report.md').write_text('\n'.join(lines).rstrip()+'\n')


def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    network=Path(args.network);input_hash=sha(network)
    selected=list(csv.DictReader(network.open()))
    assert len(selected)==len({r['station_id'] for r in selected})==50
    candidates=list(csv.DictReader(Path(args.candidates).open()))
    eligible=[r for r in candidates if int(r['both_valid_days'])*100>=70*DAYS]
    assert len(candidates)==5243 and len(eligible)==3992
    original={r['station_id']:r for r in candidates}
    for row in selected:assert all(row[k]==v for k,v in original[row['station_id']].items())
    selected.sort(key=lambda r:(int(r['both_valid_days']),r['station_id']))
    sources=json.loads(Path(args.source_provenance).read_text())['daily_sources']
    sv=vectors([float(r['longitude']) for r in selected],[float(r['latitude']) for r in selected])
    cv=vectors([float(r['longitude']) for r in candidates],[float(r['latitude']) for r in candidates])
    distances=chord_km(cdist(sv,cv))
    review=[];all_runs=[];longest_rows=[];nearby_rows=[];flags=[];flag_pairs=[];endpoint_rows=[];used_sources={}
    for number,station in enumerate(selected,1):
        sid=station['station_id'];meta=sources.get(sid)
        path=Path(args.daily_cache)/meta['cache_file'] if meta else None
        if path is None or not path.is_file():raise FileNotFoundError(f'Canonical cached source unavailable: {sid}; no download attempted')
        assert sha(path)==meta['sha256'],sid
        used_sources[sid]=meta
        inspection,runs,longest=inspect_daily(path,sid)
        standard,_=analyze_daily(path,sid,start=START,end=END)
        for key in ('total_calendar_days','valid_tmax_days','valid_tmin_days','both_valid_days','incomplete_days','longest_incomplete_run_days','qc_rejected_tmax_days','qc_rejected_tmin_days'):
            assert inspection[key]==int(station[key])==standard[key],(sid,key,inspection[key],station[key],standard[key])
        assert sum(r['days'] for r in runs)==inspection['incomplete_days']
        row={**station,**inspection,'review_number':number,'source_status':'available_hash_verified'}
        nearby=neighbors(station,candidates,distances[number-1])
        for radius in RADII:
            for pool,eligible_only in [('neighbors',True),('all_pool_neighbors',False)]:
                for key,value in radius_summary(nearby,radius,eligible_only).items():row[f'{pool}_{radius}km_{key}']=value
        assert row['neighbors_50km_count']<=row['neighbors_100km_count']<=row['neighbors_250km_count']
        assert all(row[f'neighbors_{r}km_count']<=row[f'all_pool_neighbors_{r}km_count'] for r in RADII)
        for r in runs:all_runs.append({'review_number':number,'station_id':sid,'station_name':station['station_name'],**r})
        for r in longest:longest_rows.append({'review_number':number,'station_id':sid,'station_name':station['station_name'],**r})
        for r in nearby:nearby_rows.append({'review_number':number,'station_id':sid,'station_name':station['station_name'],**r})
        substantial_rows=substantial(station,nearby)
        if substantial_rows:
            best=min(substantial_rows,key=lambda r:(-r['candidate_both_valid_days'],r['distance_km'],r['candidate_station_id']))
            flags.append({'review_number':number,'station_id':sid,'station_name':station['station_name'],
                          'selected_completeness_percent':float(station['both_valid_percent']),**best,
                          'substantially_more_complete_candidates_within_100km':len(substantial_rows)})
            for r in substantial_rows:flag_pairs.append({'review_number':number,'station_id':sid,'station_name':station['station_name'],
                           'selected_completeness_percent':float(station['both_valid_percent']),**r})
        mismatch=False
        for element in ('tmax','tmin'):
            for endpoint in ('first','last'):
                inventory=station[f'{element}_{endpoint}_year'];observed=inspection[f'{element}_{endpoint}_observed_year']
                mismatch|=str(inventory)!=str(observed)
                endpoint_rows.append({'review_number':number,'station_id':sid,'element':element.upper(),'endpoint':endpoint,
                         'inventory_year':inventory,'first_or_last_observed_year':observed,
                         'first_or_last_valid_year':inspection[f'{element}_{endpoint}_valid_year'],
                         'inventory_matches_observed':str(inventory)==str(observed)})
        row['inventory_endpoint_mismatch']=mismatch
        review.append(row)
    summary={'analysis_start':str(START),'analysis_end':str(END),'total_calendar_days':DAYS,
      'selected_station_count':50,'candidate_pool_count':len(candidates),'eligible_70pct_candidate_count':len(eligible),
      'available_daily_files':len(used_sources),'unknown_elevations':sum(not r['elevation'] for r in review),
      'endpoint_mismatch_stations':sum(r['inventory_endpoint_mismatch'] for r in review),
      'minimum_completeness_percent':min(r['both_valid_percent'] for r in review),
      'maximum_completeness_percent':max(r['both_valid_percent'] for r in review),
      'median_completeness_percent':float(np.median([r['both_valid_percent'] for r in review])),
      'stations_with_gap_at_least_365_days':sum(r['longest_incomplete_run_days']>=365 for r in review),
      'stations_with_gap_at_least_730_days':sum(r['longest_incomplete_run_days']>=730 for r in review),
      'longest_incomplete_run_days':max(r['longest_incomplete_run_days'] for r in review),
      'stations_with_substantially_more_complete_candidate_within_100km':len(flags),
      'substantial_gain_percentage_points':5,'missing_information':[]}
    comparison=list(csv.DictReader(Path(args.geographic_comparison).open()))
    coverage=next(r for r in comparison if int(r['threshold_percent'])==70 and int(r['network_size'])==50)
    write_csv(out/'station-review.csv',review);write_csv(out/'incomplete-runs.csv',all_runs)
    write_csv(out/'longest-gaps.csv',longest_rows);write_csv(out/'nearby-candidates.csv',nearby_rows)
    write_csv(out/'stations-with-nearby-higher-completeness.csv',flags)
    write_csv(out/'substantially-more-complete-neighbors-within-100km.csv',flag_pairs)
    write_csv(out/'endpoint-checks.csv',endpoint_rows);write_csv(out/'geographic-reference.csv',[coverage])
    summary['plot_validation']=make_plots(out,review)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    report(out,review,summary,flags,coverage)
    assert sha(network)==input_hash
    provenance={'generated_at':datetime.now(timezone.utc).isoformat(),'inspection_script_sha256':sha(__file__),
      'network_input_sha256':input_hash,'candidate_input_sha256':sha(args.candidates),
      'source_provenance_sha256':sha(args.source_provenance),'daily_sources':used_sources,
      'period':[str(START),str(END)],'neighbor_pool':'70%-eligible 3992, self excluded; full 5243 also tabulated',
      'substantial_flag':'within 100 km and at least 5 percentage points higher over full period; not a replacement proposal',
      'network_unchanged':True,'no_optimization_run':True,
      'output_sha256':{str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='provenance.json'}}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print('Flagged stations:',[(r['review_number'],r['station_name'],round(r['completeness_gain_percentage_points'],2)) for r in flags])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--network',default='data/processed/geography/facility-location/networks/network-70pct-50.csv')
    p.add_argument('--candidates',default='data/processed/geography/inputs/completeness-1976-2025.csv')
    p.add_argument('--source-provenance',default='data/processed/geography/inputs/source-provenance.json')
    p.add_argument('--geographic-comparison',default='data/processed/geography/facility-location/comparison.csv')
    p.add_argument('--daily-cache',default='data/raw/ghcnd-daily')
    p.add_argument('--output',default='data/processed/geography/network-review')
    run(p.parse_args())
