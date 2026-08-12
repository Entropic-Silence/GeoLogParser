#!/usr/bin/env python3
"""Create a new annotation pack from immutable experiment predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.annotation import save_annotation
from geologparser.annotation_proposals import proposal_from_prediction


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--panel-manifest", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.output_root.exists():
        raise FileExistsError(f"annotation pack already exists: {arguments.output_root}")
    panels = {row["panel_id"]: row for row in read_jsonl(arguments.panel_manifest)}
    predictions = read_jsonl(arguments.predictions)
    if {row["item_id"] for row in predictions} != set(panels):
        raise ValueError("prediction and panel ID sets differ")
    annotation_root = arguments.output_root / "annotations"
    annotation_root.mkdir(parents=True)
    intervals = 0
    for prediction in predictions:
        annotation = proposal_from_prediction(
            prediction, panels[prediction["item_id"]], arguments.experiment_id,
        )
        intervals += len(annotation["record"]["intervals"])
        save_annotation(annotation, annotation_root / f"{annotation['annotation_id']}.json")
    manifest = {
        "scope": "auto proposals for human correction; not Ground Truth",
        "experiment_id": arguments.experiment_id,
        "predictions_path": str(arguments.predictions),
        "predictions_sha256": sha256(arguments.predictions),
        "panel_manifest_path": str(arguments.panel_manifest),
        "panel_manifest_sha256": sha256(arguments.panel_manifest),
        "annotation_count": len(predictions), "proposed_interval_count": intervals,
        "human_verified_annotation_count": 0, "accuracy_metrics": None,
    }
    (arguments.output_root / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
