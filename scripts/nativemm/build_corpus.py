#!/usr/bin/env python3
"""Build the PaperII-NativeMM multi-task development corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.nativemm import build_nativemm_corpus


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_v001"))
    parser.add_argument("--maximum-california-documents", type=int)
    parser.add_argument(
        "--synthetic-manifest", type=Path,
        default=Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v001/manifest.jsonl"),
    )
    args = parser.parse_args()
    summary = build_nativemm_corpus(
        args.output,
        synthetic_manifest=args.synthetic_manifest,
        bgs_manifest=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl",
        bgs_analysis=ROOT / "experiments/paper2/analysis/bgs_layout_method_development_v018.json",
        california_manifests=[
            ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl",
            ROOT / "datasets/manifests/california_wcr_gold_v002.jsonl",
            ROOT / "datasets/manifests/california_wcr_gold_v003.jsonl",
        ],
        maximum_california_documents=args.maximum_california_documents,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
