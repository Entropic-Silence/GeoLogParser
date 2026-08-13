#!/usr/bin/env python3
"""Freeze pre-adjudication agreement for two completed blinded tracks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation_assignment import compare_blinded_annotation_tracks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first_annotation_root", type=Path)
    parser.add_argument("second_annotation_root", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    result = compare_blinded_annotation_tracks(
        arguments.first_annotation_root,
        arguments.second_annotation_root,
        arguments.destination,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
