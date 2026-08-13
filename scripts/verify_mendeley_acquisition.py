#!/usr/bin/env python3
"""Verify local files against a frozen Mendeley acquisition manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets.mendeley import verify_mendeley_acquisition


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    arguments = parser.parse_args()
    result = verify_mendeley_acquisition(arguments.dataset_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
