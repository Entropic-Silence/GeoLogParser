#!/usr/bin/env python3
"""Verify a structured-data audit against its acquired source files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets.structured_audit import verify_structured_dataset_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("audit_root", type=Path)
    arguments = parser.parse_args()
    result = verify_structured_dataset_audit(arguments.dataset_root, arguments.audit_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
