#!/usr/bin/env python3
"""Acquire a public Mendeley dataset from a frozen file-inventory response."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets.mendeley import acquire_frozen_mendeley_inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--doi", required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--license-id", required=True)
    parser.add_argument("--access-date")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--content-type", action="append", default=None,
        help="download only this MIME type; repeat for multiple types",
    )
    arguments = parser.parse_args()
    result = acquire_frozen_mendeley_inventory(
        arguments.inventory,
        arguments.destination,
        dataset_id=arguments.dataset_id,
        dataset_doi=arguments.doi,
        dataset_version=arguments.version,
        license_id=arguments.license_id,
        access_date=arguments.access_date,
        timeout=arguments.timeout,
        content_types=set(arguments.content_type) if arguments.content_type else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
