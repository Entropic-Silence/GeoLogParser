#!/usr/bin/env python3
"""Render selected content-manifest pages for independent human source review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.page_review import build_page_review_pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("content_manifest", type=Path, nargs="+")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--phase1-scope", default="international_candidate")
    parser.add_argument("--dpi", type=int, default=180)
    arguments = parser.parse_args()
    result = build_page_review_pack(
        arguments.content_manifest,
        arguments.output_root,
        phase1_scope=arguments.phase1_scope,
        dpi=arguments.dpi,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

