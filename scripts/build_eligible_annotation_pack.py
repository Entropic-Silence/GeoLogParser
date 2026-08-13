#!/usr/bin/env python3
"""Build immutable auto proposals from a completed source-review queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.eligible_annotation_pack import build_eligible_annotation_pack


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_root", type=Path)
    parser.add_argument("review_root", type=Path)
    parser.add_argument("eligible_manifest", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument(
        "--schema", type=Path,
        default=ROOT / "schemas/page_content_review_v001.schema.json",
    )
    arguments = parser.parse_args()
    result = build_eligible_annotation_pack(
        arguments.pack_root, arguments.review_root, arguments.eligible_manifest,
        arguments.output_root, arguments.schema,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
