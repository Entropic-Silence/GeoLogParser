#!/usr/bin/env python3
"""Generate a traceable current-status audit for duplicate annotation tracks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation_assignment import audit_annotation_assignment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("assignment_root", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    result = audit_annotation_assignment(arguments.assignment_root, arguments.destination)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
