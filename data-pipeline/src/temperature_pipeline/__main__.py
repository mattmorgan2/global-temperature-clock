"""Development entry point; deliberately does not calculate temperatures."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NOAA GHCN-Daily pipeline scaffold. No data processing is implemented."
    )
    parser.add_argument(
        "--status", action="store_true", help="Report implementation status without downloading data."
    )
    args = parser.parse_args()
    if args.status:
        print("Scaffold only: station selection and calculation methodology are pending.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
