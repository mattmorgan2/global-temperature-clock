# Global Daily Temperature Clock

A public website with an independent, reproducible NOAA GHCN-Daily data pipeline.
This repository is the source of truth. The initial scaffold publishes no
temperature estimates and includes no visual design.

## Architecture

- `website/`: minimal Astro site, built as static HTML for eventual SiteGround hosting.
- `data-pipeline/`: Python package and command-line entry point; no dependency on Astro.
- `data/raw/`: local source downloads (ignored by Git).
- `data/processed/`: local CSV, country summary and provenance (ignored by Git).
- `docs/methodology.md`: pending scientific decisions and reproducibility requirements.

The intended flow is NOAA inputs → Python processing → versioned public data →
Astro website. That integration is not implemented yet. The website must not
contain the core temperature calculations. A public output schema and transfer
step will be defined before connecting the two parts.

## Website

Use Node.js 22.12+ (Node 24 LTS recommended) and npm:

```sh
cd website
npm ci
npm run dev -- --host 0.0.0.0
```

Production build and local preview, from `website/`:

```sh
npm run build
npm run preview -- --host 0.0.0.0
```

The build output is `website/dist/`. SiteGround deployment is a future step:
upload the built static files to the configured site's document root once the
domain, hosting path and deployment credentials are established. No deployment
or server-side Node runtime is configured or required by this scaffold.

## Python pipeline workspace

Use Python 3.11+ (validated with Python 3.12). From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install setuptools==80.9.0 wheel==0.45.1
.venv/bin/python -m pip install --no-deps --no-build-isolation -e ./data-pipeline
.venv/bin/python -m temperature_pipeline --status
.venv/bin/python -m unittest discover -s data-pipeline/tests -v
```

The pipeline uses Python's standard library and has no runtime dependencies.
Tests use small local fixtures and require no NOAA access or credentials.

### First-pass station eligibility

From the repository root, fetch/cache NOAA metadata and write the eligible list:

```sh
.venv/bin/python -m temperature_pipeline eligible-stations
```

The default target is the current **UTC calendar year**, evaluated at run time.
A station qualifies only when **both** TMAX and TMIN inventory records have a
first year <= 1926 and a last year >= the target year. This is an endpoint filter:
it does **not** establish day-by-day or year-by-year completeness, uninterrupted
operation, quality, station-location stability, or suitability for a global
estimate. It neither selects the final 50 stations nor calculates temperatures.

Outputs in `data/processed/eligibility/`:

- `qualifying-stations.csv`: all qualifying IDs, station/country names, station
  coordinates, elevation in metres, and each element's first/last years.
  Missing elevation (NOAA sentinel -999.9) is an empty CSV field.
- `summary.json`: target year, total stations, country count and counts by country;
  also printed to the terminal.
- `provenance.json`: source URLs, retrieval times, SHA-256 hashes, HTTP validators,
  parameters, Python version, Git revision/dirty status, and output CSV hash.

The CSV is sorted by station ID; country summaries are sorted by country code.
Cache snapshots under `data/raw/ghcnd/` are named by content hash. Per-source JSON
pointers select the latest locally downloaded snapshot. Existing cached inputs
are reused and their hashes verified; they are not automatically fresh NOAA data.
To deliberately fetch current files, or replay a cached snapshot for a fixed year:

```sh
.venv/bin/python -m temperature_pipeline eligible-stations --refresh
.venv/bin/python -m temperature_pipeline eligible-stations --offline --year 2026
```

The explicit year is a replay option, not the default. Use `--cache-dir PATH` and
`--output-dir PATH` to isolate runs. Preserve the three cache pointers, their
referenced snapshots, provenance, and the code used for a run to reproduce it.
NOAA can update files independently; retrieval times record this, and a refresh
is not an atomic NOAA-wide snapshot. Network/TLS errors fail the command rather
than silently using old inputs. Download access requires `www.ncei.noaa.gov`.

Raw downloads and generated outputs stay ignored by Git. Review the small CSV,
summary and provenance together before deliberately adding any result; never
force-add the raw cache. Code, tests, configuration and methodology live in
GitHub. The website remains independent and is not wired to these outputs.

## Scientific status

The first-pass metadata eligibility filter is implemented. Final station
selection and the temperature calculation methodology remain **pending**.
See [methodology decisions](docs/methodology.md). Reproducibility will require
recorded input hashes, source metadata, parameters, dependency versions and the
code revision for every published result.

## Checks

CI builds the static website with the npm lockfile and runs the Python test suite.
Run the commands above locally before committing. There are no scientific
calculation tests yet because no calculation method has been implemented.

## Second-stage daily completeness (1926–2025)

Use the committed first-pass CSV without regenerating it:

```sh
.venv/bin/python -m temperature_pipeline completeness
```

This downloads each station's NOAA `all/STATION_ID.dly` file and analyzes the
inclusive period **1926-01-01 through 2025-12-31** (36,525 calendar days). A day
is complete only if TMAX and TMIN are both present (`VALUE != -9999`) and each
has a blank GHCN quality flag. See [methodology](docs/methodology.md) for flags
and limitations. The passing pool requires at least 95% paired-valid days:
34,699 or more days, allowing at most 1,826 incomplete days. This is a coverage
threshold, not proof of an uninterrupted record or a final station selection.

Outputs under `data/processed/completeness/` (ignored until explicitly reviewed):

- `station-completeness.csv`: every input station with original metadata, valid
  TMAX/TMIN counts, paired-valid count and percentage, incomplete-day count,
  longest incomplete run, threshold result and QC rejection counts.
- `qualifying-stations-95pct.csv`: the passing rows with the same fields.
- `summary.json`: counts, passing-country distribution, completeness bins,
  median across all stations and across passers, minimum passing percentage,
  longest gaps and QC-flag counts.
- `provenance.json`: input CSV hash, per-station source URL/retrieval time/hash,
  period, validity/threshold rules, code hashes, Git state, Python version and
  output hashes.

Downloads live in the ignored `data/raw/ghcnd-daily/` cache. Successful station
metrics are checkpointed there by source hash, analysis period and analysis-code
hash. Rerunning resumes by reusing verified cached files and matching metrics;
no network request is made for a cached file by default. Four download workers
are used (set `--workers 1` through `--workers 8`). Transient failures get up to
three attempts. If any stations fail, the command exits nonzero, writes
`failures.json`, retains successes for resumption and does not replace aggregate
outputs. Existing aggregate outputs can therefore be from an earlier run; check
provenance and command success before using them.

For a deliberate NOAA update or network-free replay:

```sh
.venv/bin/python -m temperature_pipeline completeness --refresh
.venv/bin/python -m temperature_pipeline completeness --offline
```

Refresh uses HTTP conditional requests when validators are available, retaining
unchanged files on a 304 response and preserving old content-addressed snapshots
when data change. The input file, cache directory and output directory can be
set with `--input-csv`, `--cache-dir` and `--output-dir`. Preserve cache pointers,
snapshots, code and provenance together for replay. NOAA files are fetched at
different times; this is not an atomic snapshot of NOAA's archive.

## Equal-area geographic coverage

The exploratory HEALPix analysis uses frozen 1976–2025 completeness metrics,
actual station coordinates, and Natural Earth land-minus-lakes geometry.
It compares all four grid resolutions and six completeness thresholds without
selecting final stations or changing eligibility/completeness calculations.

See [analysis methods and reproduction commands](analysis/healpix/README.md)
and the [coverage report](data/processed/geography/healpix/report.md).
Code, tests, pinned dependencies, frozen inputs, maps, CSV results and provenance
are versioned; raw downloads, caches and build outputs are excluded.
