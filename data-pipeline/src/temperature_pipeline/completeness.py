"""Daily paired-temperature coverage; independent of first-pass eligibility."""

import calendar
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .metadata import BASE_URL, sha256

START = date(1926, 1, 1)
END = date(2025, 12, 31)
QC_FLAGS = 'DGIKLMNORSTWXZ'
METRIC_FIELDS = [
    'total_calendar_days', 'valid_tmax_days', 'valid_tmin_days',
    'both_valid_days', 'both_valid_percent', 'longest_incomplete_run_days',
    'incomplete_days', 'passes_95pct', 'qc_rejected_tmax_days', 'qc_rejected_tmin_days',
]


def atomic_json(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as target:
        temp = Path(target.name)
        json.dump(value, target, indent=2)
        target.write('\n')
    os.replace(temp, path)


def parse_daily(line, expected_station=None):
    """Return (station, year, month, element, [(value, mflag, qflag, sflag)]).

    Ignore padding slots beyond the actual month length, including February 29
    in non-leap years. Reject malformed records rather than inventing missing days.
    """
    line = line.rstrip('\r\n')
    if len(line) != 269:
        raise ValueError(f'Daily record must have 269 columns, got {len(line)}')
    station, year, month, element = line[:11], int(line[11:15]), int(line[15:17]), line[17:21]
    if expected_station is not None and station != expected_station:
        raise ValueError(f'Station mismatch: {station} != {expected_station}')
    days = calendar.monthrange(year, month)[1]
    values = []
    for day in range(days):
        offset = 21 + day * 8
        values.append((int(line[offset:offset + 5]), *line[offset + 5:offset + 8]))
    return station, year, month, element, values


def passes_threshold(both, total):
    # Integer comparison avoids threshold decisions based on rounded percentages.
    return both * 100 >= total * 95


def coverage_metrics(tmax, tmin):
    if not tmax or len(tmax) != len(tmin):
        raise ValueError('Coverage arrays must have equal nonzero lengths')
    both = 0
    longest = gap = 0
    for high, low in zip(tmax, tmin):
        if high and low:
            both += 1
            gap = 0
        else:
            gap += 1
            longest = max(longest, gap)
    total = len(tmax)
    return {
        'total_calendar_days': total, 'valid_tmax_days': sum(tmax),
        'valid_tmin_days': sum(tmin), 'both_valid_days': both,
        'both_valid_percent': both * 100 / total,
        'longest_incomplete_run_days': longest, 'incomplete_days': total - both,
        'passes_95pct': passes_threshold(both, total),
    }


def analyze_daily(path, station_id, start=START, end=END):
    if end < start:
        raise ValueError('Analysis end precedes start')
    total = (end - start).days + 1
    valid = {element: bytearray(total) for element in ('TMAX', 'TMIN')}
    rejected = Counter()
    flags = Counter()
    seen = set()
    with Path(path).open(encoding='ascii') as source:
        for number, line in enumerate(source, 1):
            try:
                # Non-temperature elements and years outside the analysis do not
                # affect counts, but require a complete record and matching ID.
                if len(line.rstrip('\r\n')) != 269 or line[:11] != station_id:
                    raise ValueError('Malformed daily record or station mismatch')
                year = int(line[11:15])
                element = line[17:21]
                if element not in valid or not start.year <= year <= end.year:
                    continue
                _, year, month, element, values = parse_daily(line, station_id)
                key = (year, month, element)
                if key in seen:
                    raise ValueError(f'Duplicate temperature month: {key}')
                seen.add(key)
                for day, (value, mflag, qflag, sflag) in enumerate(values, 1):
                    offset = (date(year, month, day) - start).days
                    if not 0 <= offset < total:
                        continue
                    if value == -9999:
                        continue
                    if qflag != ' ':
                        # All nonblank flags rejected, including future/unknown ones.
                        rejected[element] += 1
                        flags[qflag] += 1
                    else:
                        valid[element][offset] = 1
            except ValueError as error:
                raise ValueError(f'{path}:{number}: {error}') from error
    metrics = coverage_metrics(valid['TMAX'], valid['TMIN'])
    metrics.update(qc_rejected_tmax_days=rejected['TMAX'], qc_rejected_tmin_days=rejected['TMIN'])
    return metrics, dict(sorted(flags.items()))


def daily_source(cache_dir, station_id, refresh=False, offline=False):
    """Verified cached snapshots; optional conditional GET refresh, atomic pointers."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    pointer = cache_dir / f'{station_id}.json'
    metadata = json.loads(pointer.read_text()) if pointer.exists() else None
    cached = cache_dir / metadata['cache_file'] if metadata else None
    if cached is not None and sha256(cached) != metadata['sha256']:
        raise ValueError(f'Cache hash mismatch: {cached}')
    if cached is not None and not refresh:
        return cached, metadata
    if offline:
        raise ValueError(f'No cached daily source for {station_id}')
    url = BASE_URL + f'all/{station_id}.dly'
    headers = {}
    if metadata:
        validators = metadata.get('http_headers', {})
        if validators.get('ETag'):
            headers['If-None-Match'] = validators['ETag']
        if validators.get('Last-Modified'):
            headers['If-Modified-Since'] = validators['Last-Modified']
    for attempt in range(3):
        temp = None
        try:
            with urlopen(Request(url, headers=headers), timeout=120) as response:
                validators = {name: response.headers.get(name) for name in ('ETag', 'Last-Modified')}
                with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as target:
                    temp = Path(target.name)
                    for block in iter(lambda: response.read(1024 * 1024), b''):
                        target.write(block)
            if not temp.stat().st_size:
                raise ValueError(f'Empty daily response: {url}')
            digest = sha256(temp)
            path = cache_dir / f'{digest}-{station_id}.dly'
            os.replace(temp, path)
            metadata = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                        'cache_file': path.name, 'sha256': digest, 'http_headers': validators}
            atomic_json(pointer, metadata)
            return path, metadata
        except HTTPError as error:
            if error.code == 304 and metadata:
                return cached, metadata
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            wait = error.headers.get('Retry-After', '')
            # Respect a long retry request by failing for a later resumable run.
            if wait.isdigit() and int(wait) > 60:
                raise
            time.sleep(int(wait) if wait.isdigit() else 2 ** attempt)
        except (URLError, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)


def run_completeness(input_csv, cache_dir, output_dir, workers=4, refresh=False, offline=False):
    if refresh and offline:
        raise ValueError('--refresh and --offline cannot be combined')
    if not 1 <= workers <= 8:
        raise ValueError('Workers must be between 1 and 8')
    input_csv, cache_dir, output_dir = Path(input_csv), Path(cache_dir), Path(output_dir)
    with input_csv.open(newline='', encoding='utf-8') as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames
        stations = list(reader)
    if not fields or not {'station_id', 'country_code', 'country_name'} <= set(fields):
        raise ValueError('Input requires station_id, country_code and country_name')
    ids = [row['station_id'] for row in stations]
    if not ids or len(set(ids)) != len(ids) or any(not re.fullmatch(r'[A-Z0-9]{11}', sid) for sid in ids):
        raise ValueError('Input station IDs must be nonempty, unique and valid GHCN IDs')
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = cache_dir / 'checkpoints'
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    code_hash = sha256(Path(__file__))

    def process(station):
        sid = station['station_id']
        path, source = daily_source(cache_dir, sid, refresh, offline)
        checkpoint = checkpoint_dir / f'{sid}.json'
        key = {'source_sha256': source['sha256'], 'analysis_start': START.isoformat(),
               'analysis_end': END.isoformat(), 'code_sha256': code_hash}
        previous = json.loads(checkpoint.read_text()) if checkpoint.exists() else None
        if previous and previous['key'] == key:
            metrics, flags = previous['metrics'], previous['quality_flags']
        else:
            metrics, flags = analyze_daily(path, sid)
            atomic_json(checkpoint, {'key': key, 'metrics': metrics, 'quality_flags': flags})
        return {**station, **metrics}, source, flags

    rows, sources, flags, failures = [], {}, Counter(), {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process, station): station['station_id'] for station in stations}
        for number, future in enumerate(as_completed(futures), 1):
            sid = futures[future]
            try:
                row, source, station_flags = future.result()
                rows.append(row)
                sources[sid] = source
                flags.update(station_flags)
            except Exception as error:
                failures[sid] = f'{type(error).__name__}: {error}'
            if number % 50 == 0 or number == len(stations):
                print(f'Completeness: {number}/{len(stations)} stations; {len(failures)} errors', file=sys.stderr, flush=True)
    if failures:
        atomic_json(output_dir / 'failures.json', failures)
        raise ValueError(f'{len(failures)} stations failed; see failures.json. Cached successes retained; rerun to resume. No aggregate outputs replaced.')
    (output_dir / 'failures.json').unlink(missing_ok=True)
    rows.sort(key=lambda row: row['station_id'])
    passing = [row for row in rows if row['passes_95pct']]
    for filename, selected in [('station-completeness.csv', rows), ('qualifying-stations-95pct.csv', passing)]:
        with (output_dir / filename).open('w', newline='', encoding='utf-8') as target:
            writer = csv.DictWriter(target, fieldnames=fields + METRIC_FIELDS)
            writer.writeheader()
            writer.writerows(selected)
    counts = Counter((row['country_code'], row['country_name']) for row in passing)
    percentages = [row['both_valid_percent'] for row in rows]
    bins = [(0, 50), (50, 80), (80, 90), (90, 95), (95, 99), (99, 100)]
    distribution = [{'lower_inclusive': lower, 'upper': upper, 'upper_inclusive': upper == 100,
                     'count': sum(lower <= percent and (percent < upper or upper == 100 and percent <= upper) for percent in percentages)}
                    for lower, upper in bins]
    summary = {
        'analysis_start': START.isoformat(), 'analysis_end': END.isoformat(),
        'total_calendar_days': (END - START).days + 1,
        'first_pass_station_count': len(rows), 'second_stage_qualifying_count': len(passing),
        'passing_country_count': len(counts),
        'passing_count_by_country': [{'country_code': code, 'country_name': name, 'count': count}
                                     for (code, name), count in sorted(counts.items())],
        'completeness_distribution_all_stations': distribution,
        'median_completeness_percent_all_stations': statistics.median(percentages),
        'median_completeness_percent_passing_stations': statistics.median(row['both_valid_percent'] for row in passing) if passing else None,
        'minimum_completeness_percent_passing_stations': min(row['both_valid_percent'] for row in passing) if passing else None,
        'stations_with_100pct': sum(row['incomplete_days'] == 0 for row in rows),
        'longest_gap_days_all_stations': max(row['longest_incomplete_run_days'] for row in rows),
        'longest_gap_days_passing_stations': max((row['longest_incomplete_run_days'] for row in passing), default=None),
        'qc_rejected_values_by_flag': dict(sorted(flags.items())),
    }
    atomic_json(output_dir / 'summary.json', summary)
    def git(*args):
        result = subprocess.run(['git', *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    provenance = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'analysis_start': START.isoformat(), 'analysis_end': END.isoformat(),
        'threshold_percent': 95, 'validity_rule': 'value != -9999 and QFLAG == blank; MFLAG/SFLAG unrestricted',
        'documented_invalid_qflags': QC_FLAGS, 'unknown_nonblank_qflags': 'also invalid',
        'format_documentation_url': BASE_URL + 'readme.txt',
        'git_commit': git('rev-parse', 'HEAD'), 'git_dirty': bool(git('status', '--porcelain')),
        'python_version': platform.python_version(),
        'code_sha256': {path.name: sha256(path) for path in Path(__file__).parent.glob('*.py')},
        'input_csv': {'path': str(input_csv), 'sha256': sha256(input_csv)},
        'daily_sources': dict(sorted(sources.items())),
        'output_sha256': {name: sha256(output_dir / name) for name in
                          ('station-completeness.csv', 'qualifying-stations-95pct.csv', 'summary.json')},
    }
    atomic_json(output_dir / 'provenance.json', provenance)
    return summary
