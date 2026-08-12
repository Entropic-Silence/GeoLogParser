#!/usr/bin/env python3
"""Export a GT snapshot only if the annotation directory passes human gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation_export import export_verified_annotations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotation_root", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(export_verified_annotations(arguments.annotation_root, arguments.destination), indent=2))


if __name__ == "__main__":
    main()
