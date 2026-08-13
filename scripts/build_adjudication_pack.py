#!/usr/bin/env python3
"""Freeze duplicate-review evidence into a non-GT adjudication task pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.annotation_assignment import build_adjudication_pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("agreement_path", type=Path)
    parser.add_argument("first_annotation_root", type=Path)
    parser.add_argument("second_annotation_root", type=Path)
    parser.add_argument("output_root", type=Path)
    arguments = parser.parse_args()
    result = build_adjudication_pack(
        arguments.agreement_path,
        arguments.first_annotation_root,
        arguments.second_annotation_root,
        arguments.output_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
