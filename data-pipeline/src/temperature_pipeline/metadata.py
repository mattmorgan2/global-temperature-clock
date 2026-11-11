"""NOAA GHCN-Daily fixed-width metadata and first-pass eligibility.

Column offsets follow the GHCN-Daily readme (one-based inclusive in NOAA's
specification; zero-based slices below). Inventory ranges describe endpoints,
not completeness or continuity.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from urllib.request import urlopen

BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
FILENAMES = ("ghcnd-stations.txt", "ghcnd-inventory.txt", "ghcnd-countries.txt")


@dataclass(frozen=True)
class Station:
    station_id: str
    station_name: str
    country_code: str
    latitude: float
    longitude: float
    elevation: float | None


@dataclass(frozen=True)
class Inventory:
    station_id: str
    element: str
    first_year: int
    last_year: int


@dataclass(frozen=True)
class EligibleStation:
    station_id: str
    station_name: str
    country_code: str
    country_name: str
    latitude: float
    longitude: float
    elevation: float | None
    tmax_first_year: int
    tmax_last_year: int
    tmin_first_year: int
    tmin_last_year: int


def parse_station(line: str) -> Station:
    if len(line.rstrip("\r\n")) < 71:
        raise ValueError("Station record shorter than 71 columns")
    station_id = line[0:11]
    elevation = float(line[31:37])
    return Station(station_id, line[41:71].strip(), station_id[:2],
                   float(line[12:20]), float(line[21:30]),
                   None if elevation == -999.9 else elevation)


def parse_inventory(line: str) -> Inventory:
    if len(line.rstrip("\r\n")) < 45:
        raise ValueError("Inventory record shorter than 45 columns")
    # Parse coordinates too so a shifted/malformed record fails visibly.
    float(line[12:20])
    float(line[21:30])
    record = Inventory(line[0:11], line[31:35], int(line[36:40]), int(line[41:45]))
    if record.first_year > record.last_year:
        raise ValueError("Inventory first year exceeds last year")
    return record


def parse_country(line: str) -> tuple[str, str]:
    if len(line.rstrip("\r\n")) < 4 or line[2] != " ":
        raise ValueError("Invalid country record")
    return line[:2], line[3:].strip()


def read_records(path, parser):
    with Path(path).open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if line.strip():
                try:
                    yield parser(line)
                except ValueError as error:
                    raise ValueError(f"{path}:{number}: {error}") from error


def qualifying_stations(stations, inventory, countries, current_year):
    """Join by station ID, requiring both inclusive endpoint ranges."""
    ranges = {}
    for record in inventory:
        if record.element not in ("TMAX", "TMIN"):
            continue
        key = (record.station_id, record.element)
        if key in ranges:
            raise ValueError(f"Duplicate inventory record: {key}")
        ranges[key] = record
    result = []
    seen = set()
    for station in stations:
        if station.station_id in seen:
            raise ValueError(f"Duplicate station: {station.station_id}")
        seen.add(station.station_id)
        tmax = ranges.get((station.station_id, "TMAX"))
        tmin = ranges.get((station.station_id, "TMIN"))
        if not (tmax and tmin):
            continue
        if not all(r.first_year <= 1926 and r.last_year >= current_year for r in (tmax, tmin)):
            continue
        if station.country_code not in countries:
            raise ValueError(f"Missing country: {station.country_code}")
        result.append(EligibleStation(
            station.station_id, station.station_name, station.country_code,
            countries[station.country_code], station.latitude, station.longitude,
            station.elevation, tmax.first_year, tmax.last_year, tmin.first_year, tmin.last_year,
        ))
    missing = {station_id for station_id, _ in ranges} - seen
    if missing:
        raise ValueError(f"Inventory references {len(missing)} stations missing from station metadata")
    return sorted(result, key=lambda station: station.station_id)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cached_source(cache_dir, filename, refresh=False, offline=False):
    """Retain immutable content-addressed snapshots and an atomic latest pointer."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    pointer = cache_dir / f"{filename}.json"
    if pointer.exists() and not refresh:
        metadata = json.loads(pointer.read_text())
        path = cache_dir / metadata["cache_file"]
        if sha256(path) != metadata["sha256"]:
            raise ValueError(f"Cache hash mismatch: {path}; refresh from NOAA")
        return path, metadata
    if offline:
        raise ValueError(f"No cached source available for {filename}")
    url = BASE_URL + filename
    temp_path = None
    try:
        with urlopen(url, timeout=120) as response, tempfile.NamedTemporaryFile(
            dir=cache_dir, delete=False
        ) as target:
            temp_path = Path(target.name)
            for block in iter(lambda: response.read(1024 * 1024), b""):
                target.write(block)
            headers = {name: response.headers.get(name) for name in ("ETag", "Last-Modified")}
        if not temp_path.stat().st_size:
            raise ValueError(f"Empty NOAA response: {url}")
        digest = sha256(temp_path)
        path = cache_dir / f"{digest}-{filename}"
        os.replace(temp_path, path)
        metadata = {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": digest, "cache_file": path.name, "http_headers": headers}
        pointer_tmp = pointer.with_suffix(".json.tmp")
        pointer_tmp.write_text(json.dumps(metadata, indent=2) + "\n")
        os.replace(pointer_tmp, pointer)
        return path, metadata
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def run(cache_dir, output_dir, year=None, refresh=False, offline=False):
    if refresh and offline:
        raise ValueError("--refresh and --offline cannot be combined")
    year = datetime.now(timezone.utc).year if year is None else year
    if year < 1926:
        raise ValueError("Target year must be 1926 or later")
    sources = {}
    paths = {}
    for filename in FILENAMES:
        paths[filename], sources[filename] = cached_source(cache_dir, filename, refresh, offline)
    countries = dict(read_records(paths["ghcnd-countries.txt"], parse_country))
    rows = qualifying_stations(
        read_records(paths["ghcnd-stations.txt"], parse_station),
        read_records(paths["ghcnd-inventory.txt"], parse_inventory), countries, year,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "qualifying-stations.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(EligibleStation.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    counts = Counter((row.country_code, row.country_name) for row in rows)
    summary = {
        "target_year": year, "total_qualifying_stations": len(rows),
        "country_count": len(counts),
        "by_country": [{"country_code": code, "country_name": name, "count": count}
                       for (code, name), count in sorted(counts.items())],
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "git_commit": revision.stdout.strip() if revision.returncode == 0 else None,
        "git_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        "criteria": {"first_year_at_most": 1926, "last_year_at_least": year,
                     "elements": ["TMAX", "TMIN"]},
        "sources": sources, "output_sha256": sha256(csv_path),
    }
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return summary
