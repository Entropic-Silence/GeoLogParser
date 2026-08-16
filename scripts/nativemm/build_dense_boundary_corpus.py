#!/usr/bin/env python3
"""Build corrected dense boundary supervision for PaperII-NativeMM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.nativemm.dense_data import build_dense_boundary_corpus


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=Path("/data/GeoLogParser/datasets/paper2_nativemm_dense_boundary_v001"),
    )
    parser.add_argument(
        "--nativemm-corpus-root", type=Path,
        default=Path("/data/GeoLogParser/datasets/paper2_nativemm_v002r2"),
    )
    args = parser.parse_args()
    summary = build_dense_boundary_corpus(
        args.output,
        nativemm_corpus_root=args.nativemm_corpus_root,
        bgs_manifest=ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl",
        bgs_analysis=ROOT / "experiments/paper2/analysis/bgs_layout_method_development_v018.json",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
