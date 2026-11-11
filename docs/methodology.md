# Methodology decisions pending

NOAA GHCN-Daily is the intended observation source. No final station-selection
method or global temperature calculation has been selected or implemented.

Before publishing estimates, explicitly decide and document:

- Station inclusion, geographic coverage, station history and eligibility rules.
- Measurement variables, units, quality flags and missing-data handling.
- Daily time boundaries, reporting delays and later revisions.
- Spatial weighting, aggregation, baseline (if used) and uncertainty reporting.
- Validation against independent references and limitations of coverage.

Reproducibility requirements for the future pipeline:

- Preserve source URLs, retrieval timestamps, source versions and SHA-256 hashes.
- Record the Git commit, Python version, dependency versions and all parameters.
- Keep raw inputs immutable; make each transformation explicit and testable.
- Publish a versioned output schema with units, provenance, coverage and limitations.
- Provide a documented command that recreates an output from recorded inputs.

These are requirements for future implementation, not claims that the scaffold
currently downloads, validates or processes NOAA observations.
