#!/usr/bin/env python3
"""Verify page content/privacy reviews and optionally export eligible pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.page_review import audit_page_reviews


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_root", type=Path)
    parser.add_argument("review_root", type=Path)
    parser.add_argument("--eligible-manifest", type=Path)
    parser.add_argument(
        "--schema", type=Path,
        default=ROOT / "schemas/page_content_review_v001.schema.json",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = audit_page_reviews(
        arguments.pack_root,
        arguments.review_root,
        arguments.schema,
        eligible_manifest=arguments.eligible_manifest,
    )
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
