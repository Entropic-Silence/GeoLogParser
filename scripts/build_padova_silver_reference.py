#!/usr/bin/env python3
"""Build an immutable Padova field-level machine-adjudicated Silver reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.silver_adjudication import build_padova_silver


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "results" / "2026-08-12"
DEFAULT_DATA = Path("/data/GeoLogParser")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_DATA / "artifacts/silver/unipd_field_silver_v001")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_DATA / "datasets/public/unipd_levee_geotech_v001/metadata/manifest.jsonl")
    parser.add_argument("--panel-manifest", type=Path, default=DEFAULT_DATA / "artifacts/annotation/unipd_levee_geotech_v001/panel_manifest.jsonl")
    parser.add_argument("--extractor-a", type=Path, default=DEFAULT_BASE / "P1_B2_QWEN3VL4B_TEXT_UNIPD_AUDIT_003/predictions.jsonl")
    parser.add_argument("--extractor-b", type=Path, default=DEFAULT_BASE / "P1_B4_QWEN3VL4B_UNIPD_AUDIT_001/predictions.jsonl")
    parser.add_argument("--layout", type=Path, default=DEFAULT_BASE / "P1_B3_LAYOUT_UNIPD_AUDIT_002/predictions.jsonl")
    parser.add_argument("--without-layout", action="store_true", help="Build A/B-only reference; use layout as a held-out corroboration channel.")
    args = parser.parse_args()
    layout = None if args.without_layout else args.layout
    summary = build_padova_silver(args.output, source_manifest=args.source_manifest, panel_manifest=args.panel_manifest, extractor_a_path=args.extractor_a, extractor_b_path=args.extractor_b, layout_path=layout)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
