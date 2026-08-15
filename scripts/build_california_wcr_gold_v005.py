#!/usr/bin/env python3
"""Freeze California WCR v005 after excluding v001--v004.

The acquisition logic is reused from the v004 builder; metadata and split
labels are rewritten so the resulting freeze is independently versioned.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_california_wcr_gold_v004 import main as build_v004

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wcr", type=Path)
    parser.add_argument("--lithology", type=Path)
    parser.add_argument("--target-documents", type=int, default=100)
    args = parser.parse_args()
    dataset_root = Path("/data/GeoLogParser/datasets/public/california_wcr_gold_v005")
    manifest = (ROOT / "datasets/manifests/california_wcr_gold_v005.jsonl").resolve()
    split = (ROOT / "datasets/splits/california_wcr_gold_split_v005.json").resolve()
    argv = [
        "--dataset-root", str(dataset_root),
        "--manifest", str(manifest),
        "--split", str(split),
        "--target-documents", str(args.target_documents),
    ]
    if args.wcr:
        argv += ["--wcr", str(args.wcr)]
    if args.lithology:
        argv += ["--lithology", str(args.lithology)]
    for version in (1, 2, 3, 4):
        argv += ["--exclude-manifest", str(ROOT / f"datasets/manifests/california_wcr_gold_v00{version}.jsonl")]
    import sys
    old = sys.argv
    try:
        sys.argv = ["build_california_wcr_gold_v004.py", *argv]
        build_v004()
    finally:
        sys.argv = old
    metadata_path = dataset_root / "metadata" / "acquisition.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["dataset_version"] = "california_wcr_gold_v005"
    metadata["selection_version"] = "v001_order_successor_excluding_v001_v002_v003_v004"
    metadata["prospective_for_policy"] = "independent_external_replication_only"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    split_obj = json.loads(split.read_text(encoding="utf-8"))
    split_obj["split_version"] = "california_wcr_gold_split_v005_external_replication"
    split_obj["policy"] = "Next deterministic clean candidates after excluding v001-v004; no method or policy development."
    split.write_text(json.dumps(split_obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
