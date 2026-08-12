#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from geologparser.datasets.bgs import download_fixed_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Download an explicit fixed-ID BGS OGL sample")
    parser.add_argument("--ids", nargs="+", type=int, required=True)
    parser.add_argument("--root", type=Path, default=Path("/data/GeoLogParser/datasets/public/bgs_v001"))
    parser.add_argument("--access-date")
    arguments = parser.parse_args()
    print(download_fixed_sample(arguments.ids, arguments.root, arguments.access_date))


if __name__ == "__main__":
    main()

