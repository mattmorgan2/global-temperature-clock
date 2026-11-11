# Global Daily Temperature Clock

A public website with an independent, reproducible NOAA GHCN-Daily data pipeline.
This repository is the source of truth. The initial scaffold publishes no
temperature estimates and includes no visual design.

## Architecture

- `website/`: minimal Astro site, built as static HTML for eventual SiteGround hosting.
- `data-pipeline/`: Python package and command-line entry point; no dependency on Astro.
- `data/raw/`: local source downloads (ignored by Git).
- `data/processed/`: local pipeline outputs (ignored by Git).
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

The pipeline has no runtime dependencies yet. Its CLI only reports scaffold
status; it does not download data or calculate temperatures. No credentials or
external services are required for these checks. Source data and generated
outputs stay out of Git; code, configuration, lockfiles and methodology belong
in GitHub. Future data releases need a separately documented publication policy.

## Scientific status

Station selection and the final calculation methodology remain **pending**.
See [methodology decisions](docs/methodology.md). Reproducibility will require
recorded input hashes, source metadata, parameters, dependency versions and the
code revision for every published result.

## Checks

CI builds the static website with the npm lockfile and runs the Python CLI test.
Run the commands above locally before committing. There are no scientific
calculation tests yet because no calculation method has been implemented.
