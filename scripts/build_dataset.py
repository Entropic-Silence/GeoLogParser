#!/usr/bin/env python3
"""Build versioned random/group-disjoint split manifests from a dataset JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.datasets import split_manifest


SPLITS = {
    "random_page": ("random_page_v001", None),
    "project_disjoint": ("project_disjoint_v001", "project_id"),
    "template_disjoint": ("template_disjoint_v001", "template_id"),
    "source_disjoint": ("source_disjoint_v001", "source_id"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--ratios", nargs=3, type=float, default=(.7, .1, .2), metavar=("TRAIN", "VALIDATION", "TEST"))
    parser.add_argument("--splits", nargs="+", choices=tuple(SPLITS), default=tuple(SPLITS))
    arguments = parser.parse_args()
    records = [json.loads(line) for line in arguments.source_manifest.read_text(encoding="utf-8").splitlines() if line]
    if not records:
        raise ValueError("source manifest is empty")
    if any("record_id" not in record for record in records):
        raise ValueError("every record requires record_id")
    if len({str(record["record_id"]) for record in records}) != len(records):
        raise ValueError("record_id values must be unique")
    ratios = dict(zip(("train", "validation", "test"), arguments.ratios))
    arguments.output_directory.mkdir(parents=True, exist_ok=False)
    summary = {"source_manifest": str(arguments.source_manifest.resolve()), "records": len(records), "splits": {}}
    for name in arguments.splits:
        split_type, group_key = SPLITS[name]
        result = split_manifest(records, split_type, group_key, ratios, arguments.seed)
        path = arguments.output_directory / f"{name}_v001.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary["splits"][name] = {"path": str(path), "counts": result["counts"], "group_key": group_key}
    (arguments.output_directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
