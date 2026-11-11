"""Command-line metadata eligibility workflow; no temperature calculations."""

import argparse
import json
from pathlib import Path

from .metadata import run


def main() -> None:
    parser = argparse.ArgumentParser(description="NOAA GHCN-Daily metadata eligibility filter.")
    parser.add_argument("--status", action="store_true", help="Report implementation status without downloading.")
    commands = parser.add_subparsers(dest="command")
    eligible = commands.add_parser("eligible-stations", help="Build the first-pass station list.")
    eligible.add_argument("--cache-dir", type=Path, default=Path("data/raw/ghcnd"))
    eligible.add_argument("--output-dir", type=Path, default=Path("data/processed/eligibility"))
    eligible.add_argument("--year", type=int, help="Override current UTC calendar year for reproducibility.")
    mode = eligible.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="Fetch new NOAA snapshots.")
    mode.add_argument("--offline", action="store_true", help="Require cached inputs; never download.")
    args = parser.parse_args()
    if args.status:
        print("Metadata eligibility filter implemented; final station selection and calculation methodology are pending.")
    elif args.command == "eligible-stations":
        try:
            summary = run(args.cache_dir, args.output_dir, args.year, args.refresh, args.offline)
        except (ValueError, OSError) as error:
            parser.exit(1, f"Eligibility pipeline failed: {error}\n")
        print(json.dumps(summary, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
