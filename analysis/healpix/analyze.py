#!/usr/bin/env python3
"""Exploratory HEALPix coverage; never selects a final station network."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/ghcn-healpix-mpl')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/ghcn-healpix-cache')
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import shutil
import sys
from urllib.request import urlopen

import healpy as hp
import numpy as np
from pyproj import Geod
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist, squareform
import shapely
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, shape, box
from shapely.affinity import translate
from shapely.strtree import STRtree

R = 6371.0088  # IUGG mean Earth radius, km; spherical HEALPix and distances
GEOD = Geod(a=R * 1000, b=R * 1000)
THRESHOLDS = (70, 75, 80, 85, 90, 95)
NSIDES = (1, 2, 4, 8)
SEED = 20261111
NE_COMMIT = 'ca96624a56bd078437bca8184e78163e5039ad19'
NE_BASE = f'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson/'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def write_csv(path, rows):
    rows = list(rows)
    if not rows: return
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def parts(geom):
    if isinstance(geom, Polygon):
        if not geom.is_empty: yield geom
    elif hasattr(geom, 'geoms'):
        for item in geom.geoms: yield from parts(item)


def spherical_area(geom):
    total = 0.
    for poly in parts(geom):
        x, y = poly.exterior.xy
        area = abs(GEOD.polygon_area_perimeter(x, y)[0])
        for ring in poly.interiors:
            x, y = ring.xy; area -= abs(GEOD.polygon_area_perimeter(x, y)[0])
        total += area / 1e6
    return total


def pixel_polygon(nside, pixel, step=256):
    """Densify HEALPix curved edges; unwrap about center, duplicate pole longitude."""
    lon, lat = hp.vec2ang(hp.boundaries(nside, pixel, step=step, nest=True).T, lonlat=True)
    center = hp.pix2ang(nside, pixel, nest=True, lonlat=True)[0]
    center = (center + 180) % 360 - 180
    lon = center + (lon - center + 180) % 360 - 180
    coords = []
    for i, (x, y) in enumerate(zip(lon, lat)):
        if abs(y) > 89.999999:
            coords.extend([(lon[i - 1], y), (lon[(i + 1) % len(lon)], y)])
        else: coords.append((x, y))
    result = Polygon(coords)
    if not result.is_valid: raise ValueError(f'Invalid pixel geometry: {nside}/{pixel}')
    return result


def vectors(lon, lat):
    return hp.ang2vec(np.asarray(lon), np.asarray(lat), lonlat=True)


def chord_km(chord):
    return 2 * R * np.arcsin(np.clip(np.asarray(chord) / 2, 0, 1))


def distance_stats(values, prefix=''):
    values = np.asarray(values)
    values = values[np.isfinite(values)]
    if not len(values): return {prefix + 'count': 0}
    ps = np.percentile(values, [0, 5, 25, 50, 75, 90, 95, 99, 100])
    return {prefix + 'count': int(len(values)), prefix + 'mean_km': float(values.mean()),
            **{prefix + key + '_km': float(x) for key, x in zip(('min','p05','p25','p50','p75','p90','p95','p99','max'), ps)}}


def boundary_distance_km(point, poly):
    """Spherical distance to densified boundary arcs, including endpoint checks."""
    xy = np.asarray(poly.exterior.coords)
    vv = vectors(xy[:, 0], xy[:, 1]); a, b = vv[:-1], vv[1:]
    normal = np.cross(a, b); norm = np.linalg.norm(normal, axis=1)
    valid = norm > 1e-14; a, b, normal, norm = a[valid], b[valid], normal[valid], norm[valid]
    normal = normal / norm[:, None]
    foot = point - (normal @ point)[:, None] * normal
    foot /= np.maximum(np.linalg.norm(foot, axis=1)[:, None], 1e-30)
    angle = lambda u, v: np.arccos(np.clip(np.sum(u * v, axis=-1), -1, 1))
    on_arc = np.abs(angle(a, foot) + angle(foot, b) - angle(a, b)) < 1e-7
    distance = np.minimum(angle(a, point), angle(b, point))
    distance[on_arc] = angle(foot[on_arc], point)
    return float(distance.min() * R)


def load_land(raw):
    """Natural Earth 1:10m land minus lakes/reservoirs; no country boundaries."""
    raw.mkdir(parents=True, exist_ok=True)
    sources = {}
    datasets = {}
    for name in ('ne_10m_land.geojson', 'ne_10m_lakes.geojson'):
        path = raw / name
        if not path.exists():
            with urlopen(NE_BASE + name, timeout=120) as r, path.open('wb') as f: shutil.copyfileobj(r, f)
        sources[name] = {'url': NE_BASE + name, 'sha256': digest(path), 'bytes': path.stat().st_size}
        data = json.loads(path.read_text())
        datasets[name] = [poly for feature in data['features'] for poly in parts(shape(feature['geometry']))]
    lakes = np.asarray(datasets['ne_10m_lakes.geojson'], dtype=object)
    lake_tree = STRtree(lakes)
    land_parts = []
    for poly in datasets['ne_10m_land.geojson']:
        hits = lake_tree.query(poly, predicate='intersects')
        clipped = poly.difference(shapely.union_all(lakes[hits])) if len(hits) else poly
        land_parts.extend(parts(clipped))
    if not all(poly.is_valid for poly in land_parts): raise ValueError('Invalid land geometry')
    # 360-degree copies permit dateline-safe clipping of unwrapped HEALPix cells.
    copies = np.asarray([translate(poly, xoff=shift) for shift in (-360, 0, 360) for poly in land_parts], dtype=object)
    return land_parts, STRtree(copies), copies, sources


def clip_grid(nside, tree, copies, step):
    areas, clips, pixels = [], [], []
    for pixel in range(hp.nside2npix(nside)):
        poly = pixel_polygon(nside, pixel, step)
        hits = tree.query(poly, predicate='intersects')
        clipped = shapely.union_all(shapely.intersection(copies[hits], poly)) if len(hits) else GeometryCollection()
        areas.append(spherical_area(clipped)); clips.append(clipped); pixels.append(poly)
    return np.asarray(areas), clips, pixels


def sample_land(nside, land_parts, raw, signature):
    path = raw / f'land-centers-nside-{nside}-{signature[:12]}.npz'
    if path.exists(): return np.load(path)['pixels']
    land = shapely.union_all(land_parts); shapely.prepare(land)
    selected = []
    for lo in range(0, hp.nside2npix(nside), 250000):
        ids = np.arange(lo, min(lo + 250000, hp.nside2npix(nside)), dtype=np.int64)
        lon, lat = hp.pix2ang(nside, ids, nest=True, lonlat=True)
        lon = (lon + 180) % 360 - 180
        mask = shapely.contains_xy(land, lon, lat)
        selected.append(ids[mask].astype(np.int32))
    result = np.concatenate(selected)
    np.savez_compressed(path, pixels=result)
    return result


def world_pieces(geom):
    for shift in (-360, 0, 360):
        g = geom.intersection(box(-180 + shift, -90, 180 + shift, 90))
        if not g.is_empty: yield translate(g, xoff=-shift)


def mpl_path(geom):
    from matplotlib.path import Path as MplPath
    vertices, codes = [], []
    for g in world_pieces(geom):
        for poly in parts(shapely.orient_polygons(g)):
            for ring in (poly.exterior, *poly.interiors):
                xy = np.radians(np.asarray(ring.coords))
                cc = np.full(len(xy), MplPath.LINETO, dtype=np.uint8)
                cc[0] = MplPath.MOVETO; cc[-1] = MplPath.CLOSEPOLY
                vertices.append(xy); codes.append(cc)
    return MplPath(np.vstack(vertices), np.concatenate(codes)) if vertices else None


def make_maps(output, grids, station_lon, station_lat, both, days):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch, Patch
    output.mkdir(exist_ok=True)
    colors = {'occupied': '#16856b', 'empty': '#e8a140', 'ocean': '#dcecf6'}
    for nside, (areas, clips, pixels) in grids.items():
        paths = [mpl_path(g) if area > 1e-9 else None for g, area in zip(clips, areas)]
        borderpaths = [mpl_path(g) for g in pixels]
        figure, axes = plt.subplots(3, 1, figsize=(13, 20), subplot_kw={'projection':'mollweide'})
        for ax, threshold in zip(axes, (70, 85, 95)):
            valid = both * 100 >= days * threshold
            labels = hp.ang2pix(nside, station_lon[valid], station_lat[valid], nest=True, lonlat=True)
            counts = np.bincount(labels, minlength=len(areas))
            ax.set_facecolor(colors['ocean'])
            for pixel, path in enumerate(paths):
                if path is not None: ax.add_patch(PathPatch(path, facecolor=colors['occupied' if counts[pixel] else 'empty'], edgecolor='none', rasterized=True))
            for path in borderpaths:
                if path is not None: ax.add_patch(PathPatch(path, facecolor='none', edgecolor='#536774', linewidth=.27, alpha=.55))
            lon = (station_lon[valid] + 180) % 360 - 180
            ax.scatter(np.radians(lon), np.radians(station_lat[valid]), s=1.5, c='#111111', alpha=.4, linewidth=0, rasterized=True)
            ax.grid(alpha=.15); ax.set_xticklabels([]); ax.set_yticklabels([])
            land_count = int((areas > 1e-9).sum()); occ = int(((areas > 1e-9) & (counts > 0)).sum())
            represented = float(areas[counts > 0].sum() / areas.sum() * 100)
            ax.set_title(f'{hp.nside2npix(nside)} global cells | completeness ≥{threshold}% | {occ}/{land_count} land cells occupied | {represented:.1f}% land in occupied cells', fontsize=11)
        axes[-1].legend(handles=[Patch(color=colors['occupied'], label='Land in occupied cell'), Patch(color=colors['empty'], label='Land in empty cell'), Patch(color=colors['ocean'], label='Ocean / inland water')], loc='lower center', bbox_to_anchor=(.5, -.20), ncol=3, fontsize=9)
        figure.suptitle('GHCN-Daily 1976–2025 · Natural Earth 1:10m land minus lakes · HEALPix NESTED\nDots are all qualifying candidates; cell shading is a coverage proxy, not a station selection.', fontsize=12, y=.985)
        figure.subplots_adjust(hspace=.22, top=.945, bottom=.055)
        figure.savefig(output / f'healpix-{hp.nside2npix(nside)}-cells.png', dpi=160, facecolor='white')
        for axis in axes: axis.set_rasterized(True)
        figure.savefig(output / f'healpix-{hp.nside2npix(nside)}-cells.pdf', dpi=160, facecolor='white')
        plt.close(figure)


def run(args):
    out, raw = Path(args.output), Path(args.raw)
    out.mkdir(parents=True, exist_ok=True); raw.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(Path(args.stations).open()))
    if not rows: raise ValueError('No stations')
    if len({r['station_id'] for r in rows}) != len(rows): raise ValueError('Duplicate station IDs')
    lon = np.array([float(r['longitude']) for r in rows]); lat = np.array([float(r['latitude']) for r in rows])
    both = np.array([int(r['both_valid_days']) for r in rows]); days = np.array([int(r['total_calendar_days']) for r in rows])
    if not np.all(days == 18263): raise ValueError('Expected 1976–2025 metrics: 18,263 days')
    if not np.all((abs(lat) <= 90) & (abs(lon) <= 180)): raise ValueError('Invalid coordinates')
    land_parts, tree, copies, sources = load_land(raw)
    source_signature = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    land_geom = shapely.union_all(land_parts); shapely.prepare(land_geom)
    on_land = shapely.contains_xy(land_geom, lon, lat)
    total_land_area = sum(spherical_area(g) for g in land_parts)
    grids, grid_validation = {}, []
    for nside in NSIDES:
        print(f'Clipping HEALPix NSIDE {nside}', flush=True)
        areas, clips, pixels = clip_grid(nside, tree, copies, args.boundary_step)
        coarse, _, _ = clip_grid(nside, tree, copies, args.boundary_step // 2)
        ideal = 4 * np.pi * R**2 / hp.nside2npix(nside)
        max_cell_error = max(abs(spherical_area(g)/ideal - 1) for g in pixels)
        relative_error = abs(areas.sum()/total_land_area - 1)
        relative_convergence = abs(areas-coarse).sum()/total_land_area
        if max_cell_error > 5e-5 or relative_error > 5e-5 or relative_convergence > 5e-5:
            raise AssertionError(f'Grid area/convergence check failed: {nside} {max_cell_error} {relative_error} {relative_convergence}')
        grids[nside] = (areas, clips, pixels)
        grid_validation.append({'nside':nside, 'land_area_km2':float(areas.sum()), 'global_land_relative_error':float(relative_error), 'max_pixel_area_relative_error':float(max_cell_error), 'boundary_convergence_relative_land_error':float(relative_convergence), 'land_cell_count_change_on_doubling_boundary_step':int(np.count_nonzero(areas>1e-9)-np.count_nonzero(coarse>1e-9))})
    assignments=[]
    pixel_arrays={n:hp.ang2pix(n,lon,lat,nest=True,lonlat=True) for n in NSIDES}
    for i,r in enumerate(rows):
        assignments.append({**r, 'station_point_on_land_mask':bool(on_land[i]), **{f'healpix_nside_{n}_nested':int(pixel_arrays[n][i]) for n in NSIDES}, **{f'qualifies_{t}pct':bool(both[i]*100>=days[i]*t) for t in THRESHOLDS}})
    write_csv(out/'station-cell-assignments.csv',assignments)
    print('Sampling land with fine equal-area HEALPix centers',flush=True)
    samples=sample_land(args.sample_nside,land_parts,raw,source_signature)
    sample_lon,sample_lat=hp.pix2ang(args.sample_nside,samples,nest=True,lonlat=True)
    sample_vec=vectors(sample_lon,sample_lat)
    coarse_samples=sample_land(args.sample_nside//2,land_parts,raw,source_signature)
    c_lon,c_lat=hp.pix2ang(args.sample_nside//2,coarse_samples,nest=True,lonlat=True)
    coarse_vec=vectors(c_lon,c_lat)
    sim_rng=np.random.default_rng(SEED)
    sim_ids=sim_rng.choice(len(samples), min(args.simulation_land_points,len(samples)),replace=False)
    simulation_vec=sample_vec[sim_ids]
    np.savez_compressed(out/'land-distance-sample.npz',nside=args.sample_nside,pixels=samples,simulation_indices=sim_ids)
    coverage,cell_rows,spacing,neighbor_rows,land_stats,simulation_rows,sampling_validation=[],[],[],[],[],[],[]
    for threshold in THRESHOLDS:
        mask=both*100>=days*threshold
        ids=np.flatnonzero(mask); sv=vectors(lon[ids],lat[ids])
        print(f'Analyzing completeness ≥{threshold}%: {len(ids)} stations',flush=True)
        tree_station=cKDTree(sv)
        nearest=chord_km(tree_station.query(sample_vec,workers=args.workers)[0])
        coarse_nearest=chord_km(tree_station.query(coarse_vec,workers=args.workers)[0])
        stats=distance_stats(nearest)
        land_stats.append({'threshold_percent':threshold,'qualifying_stations':len(ids),**stats})
        sampling_validation.append({'threshold_percent':threshold,'fine_nside':args.sample_nside,'coarse_nside':args.sample_nside//2,'p50_distance_change_km':float(np.median(nearest)-np.median(coarse_nearest)), 'p95_distance_change_km':float(np.percentile(nearest,95)-np.percentile(coarse_nearest,95))})
        all_dist=squareform(chord_km(pdist(sv)))
        triangle=np.triu_indices(len(ids),1)
        flat_dist=all_dist[triangle]
        for nside,(areas,clips,pixels) in grids.items():
            labels=pixel_arrays[nside][ids]; npix=len(areas)
            counts=np.bincount(labels,minlength=npix)
            land=areas>1e-9; occupied=land&(counts>0); occ=np.flatnonzero(occupied)
            if not len(occ): raise ValueError('No occupied land cells')
            c=counts[occupied]
            same=labels[:,None]==labels[None,:]
            nearest_cross=np.min(np.where(same,np.inf,all_dist),axis=1)
            cross=labels[triangle[0]]!=labels[triangle[1]]
            scale=math.sqrt(4*np.pi*R**2/npix)
            neighbours=[]
            groups={int(p):np.flatnonzero(labels==p) for p in occ}
            for a in occ:
                for b in hp.get_all_neighbours(nside,int(a),nest=True):
                    b=int(b)
                    if b<=a or b not in groups:continue
                    ai,bi=groups[int(a)],groups[b]
                    block=all_dist[np.ix_(ai,bi)]
                    ix=np.unravel_index(np.argmin(block),block.shape)
                    ii,jj=int(ai[ix[0]]),int(bi[ix[1]])
                    closest=float(block[ix]); da=boundary_distance_km(sv[ii],pixels[int(a)]);db=boundary_distance_km(sv[jj],pixels[b])
                    r={'global_cells':npix,'threshold_percent':threshold,'cell_a':int(a),'cell_b':b,
                       'closest_station_a':rows[ids[ii]]['station_id'],'closest_station_b':rows[ids[jj]]['station_id'],
                       'closest_distance_km':closest,'distance_over_sqrt_cell_area':closest/scale,
                       'a_to_own_cell_boundary_km':da,'b_to_own_cell_boundary_km':db,
                       'boundary_cluster_100km_and_both_within_50km':bool(closest<=100 and da<=50 and db<=50)}
                    neighbours.append(r)
            neighbor_rows.extend(neighbours)
            coverage.append({'nside':nside,'global_cells':npix,'threshold_percent':threshold,
                'qualifying_stations':len(ids),'land_cells':int(land.sum()),'occupied_land_cells':len(occ),
                'unoccupied_land_cells':int((land&~occupied).sum()),'land_area_km2':float(areas.sum()),
                'represented_land_area_km2':float(areas[occupied].sum()),'represented_land_percent':float(100*areas[occupied].sum()/areas.sum()),
                'stations_in_occupied_land_cells':int(c.sum()),'stations_in_ocean_only_cells':int(counts[~land].sum()),
                'occupied_ocean_only_cells':int(((counts>0)&~land).sum()),'stations_outside_point_land_mask':int((~on_land[ids]).sum()),
                'singleton_occupied_land_cells':int((c==1).sum()),'stations_per_occupied_cell_min':int(c.min()),
                'stations_per_occupied_cell_p25':float(np.percentile(c,25)), 'stations_per_occupied_cell_median':float(np.median(c)),
                'stations_per_occupied_cell_p75':float(np.percentile(c,75)), 'stations_per_occupied_cell_max':int(c.max()),
                'stations_per_occupied_cell_mean':float(c.mean()),'land_cells_below_1pct_land_fraction':int((land&(areas<.01*4*np.pi*R**2/npix)).sum()),
                'land_cells_below_100km2':int((land&(areas<100)).sum())})
            spacing.append({'global_cells':npix,'threshold_percent':threshold,'nominal_sqrt_cell_area_km':scale,
                **distance_stats(flat_dist[cross],'cross_cell_pair_'),**distance_stats(nearest_cross,'nearest_other_cell_'),
                'occupied_neighbor_pairs':len(neighbours),
                **{f'neighbor_pairs_closest_within_{km}km':sum(r['closest_distance_km']<=km for r in neighbours) for km in (50,100,250)},
                'neighbor_pairs_boundary_cluster':sum(r['boundary_cluster_100km_and_both_within_50km'] for r in neighbours),
                **distance_stats([r['closest_distance_km'] for r in neighbours],'neighbor_cell_closest_')})
            for p in range(npix):
                cell_rows.append({'nside':nside,'global_cells':npix,'threshold_percent':threshold,'cell_nested':p,
                                  'land_area_km2':float(areas[p]),'land_fraction':float(areas[p]/(4*np.pi*R**2/npix)),
                                  'has_land':bool(land[p]),'candidate_stations':int(counts[p]),'occupied_land_cell':bool(occupied[p])})
            rng=np.random.default_rng(SEED+nside*1000+threshold)
            for repeat in range(args.simulations):
                chosen=np.array([rng.choice(groups[int(p)]) for p in occ])
                selected=sv[chosen]
                dd=chord_km(cKDTree(selected).query(simulation_vec,workers=args.workers)[0])
                if len(selected)>1:
                    nn=chord_km(cKDTree(selected).query(selected,k=2)[0][:,1])
                else:nn=np.array([np.nan])
                simulation_rows.append({'global_cells':npix,'threshold_percent':threshold,'repeat':repeat,'network_size':len(selected),
                    **distance_stats(dd,'land_nearest_'),**distance_stats(nn,'station_nearest_neighbor_')})
    write_csv(out/'coverage.csv',coverage);write_csv(out/'cell-coverage.csv',cell_rows)
    write_csv(out/'spacing.csv',spacing);write_csv(out/'neighbor-cell-pairs.csv',neighbor_rows)
    write_csv(out/'land-nearest-station-distances.csv',land_stats)
    write_csv(out/'one-per-cell-simulations.csv',simulation_rows)
    simulation_summary=[]
    for row in coverage:
        subset=[s for s in simulation_rows if s['global_cells']==row['global_cells'] and s['threshold_percent']==row['threshold_percent']]
        simulation_summary.append({'global_cells':row['global_cells'],'threshold_percent':row['threshold_percent'],'network_size':row['occupied_land_cells'],
          **{f'{key}_across_simulations_{stat}':float(fn([r[key] for r in subset]))
             for key in ('land_nearest_p50_km','land_nearest_p95_km','land_nearest_mean_km','station_nearest_neighbor_min_km','station_nearest_neighbor_p50_km')
             for stat,fn in [('median',np.median),('p05',lambda a:np.percentile(a,5)),('p95',lambda a:np.percentile(a,95))]}})
    write_csv(out/'one-per-cell-summary.csv',simulation_summary)
    # Reconcile every cell count and exact-threshold station count.
    for nside in NSIDES:
        subset=[r for r in coverage if r['nside']==nside]
        assert [r['qualifying_stations'] for r in subset]==[3992,3868,3725,3476,3008,2202]
        assert all(a['occupied_land_cells']>=b['occupied_land_cells'] for a,b in zip(subset,subset[1:]))
        assert all(a['represented_land_percent']>=b['represented_land_percent']-1e-9 for a,b in zip(subset,subset[1:]))
    for threshold in THRESHOLDS:
        subset=[r for r in coverage if r['threshold_percent']==threshold]
        assert all(a['represented_land_percent']>=b['represented_land_percent']-1e-3 for a,b in zip(subset,subset[1:]))
    if args.maps:
        print('Rendering world maps',flush=True)
        make_maps(out/'maps',grids,lon,lat,both,days)
    sampled_area=len(samples)*4*np.pi*R**2/hp.nside2npix(args.sample_nside)
    validation={'grid_geometry':grid_validation,'sampling_convergence':sampling_validation,
                'fine_sample_land_points':len(samples),'coarse_sample_land_points':len(coarse_samples),
                'sample_land_area_km2':sampled_area,'polygon_land_area_km2':total_land_area,
                'sampling_area_relative_difference':sampled_area/total_land_area-1,
                'duplicate_coordinate_station_ids':int(len(rows)-len(set(zip(lon,lat)))),
                'all_checks_passed':True}
    (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    provenance={'generated_at':datetime.now(timezone.utc).isoformat(),'analysis_period':['1976-01-01','2025-12-31'],
        'station_metrics_sha256':digest(args.stations),'analysis_script_sha256':digest(__file__),
        'sources':sources,'earth_radius_km':R,'healpix_ordering':'NESTED','nsides':NSIDES,'thresholds':THRESHOLDS,
        'boundary_step':args.boundary_step,'land_sample_nside':args.sample_nside,'random_seed':SEED,
        'simulations_per_configuration':args.simulations,'simulation_land_points':len(sim_ids),
        'dependencies':{name:importlib.metadata.version(name) for name in ('numpy','scipy','healpy','shapely','pyproj','matplotlib')},
        'output_sha256':{str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file() and p.suffix in ('.csv','.json','.npz','.png','.pdf') and p.name!='provenance.json'}}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'coverage':coverage,'land_distances':land_stats,'validation':validation},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stations',default='data/processed/geography/inputs/completeness-1976-2025.csv')
    p.add_argument('--raw',default='data/raw/geography')
    p.add_argument('--output',default='data/processed/geography/healpix')
    p.add_argument('--sample-nside',type=int,default=1024)
    p.add_argument('--boundary-step',type=int,default=256)
    p.add_argument('--simulations',type=int,default=32)
    p.add_argument('--simulation-land-points',type=int,default=100000)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--maps',action=argparse.BooleanOptionalAction,default=True)
    run(p.parse_args())
