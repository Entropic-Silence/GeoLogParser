#!/usr/bin/env python3
"""Create an immutable content audit for an acquired structured dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets.structured_audit import (
    SUPPORTED_PROFILES,
    build_structured_dataset_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--profile", required=True, choices=sorted(SUPPORTED_PROFILES))
    parser.add_argument("--audited-at-utc")
    arguments = parser.parse_args()
    result = build_structured_dataset_audit(
        arguments.dataset_root,
        arguments.destination,
        profile=arguments.profile,
        audited_at_utc=arguments.audited_at_utc,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
