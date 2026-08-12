#!/usr/bin/env python3
"""Fuse page-grounded proposals with VLM audit output, without claiming accuracy."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

from geologparser.constraints import default_engine
from geologparser.experiment import create_run_directory
from geologparser.extraction import fuse_records


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--annotation-root", type=Path, required=True)
    parser.add_argument("--vlm-predictions", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    vlm_rows = {
        row["item_id"]: row for row in (
            json.loads(line) for line in arguments.vlm_predictions.read_text(encoding="utf-8").splitlines() if line
        )
    }
    annotations = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(arguments.annotation_root.glob("*.json"))]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": "2026-08-12",
        "dataset_version": arguments.dataset_version,
        "split_version": "engineering_audit_no_training_no_ground_truth",
        "model": "B6_conservative_direct_text_plus_Qwen3-VL-4B",
        "model_revision": "conservative_field_fusion_v001",
        "prompt_version": "inherits_vlm_input_run",
        "seed": None,
        "hardware": {"device": "cpu_postprocessing", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "annotation_root": str(arguments.annotation_root),
            "vlm_predictions_path": str(arguments.vlm_predictions),
            "vlm_predictions_sha256": sha256(arguments.vlm_predictions),
            "dataset_manifest_path": str(arguments.dataset_manifest),
            "dataset_manifest_sha256": sha256(arguments.dataset_manifest),
            "scope": "public unannotated B6 engineering audit; no accuracy claim",
        },
    })
    started = time.perf_counter()
    rows, failures = [], []
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for annotation in annotations:
            item_id = annotation["annotation_id"]
            grounded = annotation["record"]
            vlm = vlm_rows.get(item_id)
            if vlm and vlm.get("parse_status") == "schema_valid" and vlm.get("record"):
                record, decisions = fuse_records(grounded, vlm["record"])
                visual_available = True
            else:
                record = grounded
                decisions = [{"field_path": "record", "decision": "vlm_unavailable_keep_grounded"}]
                visual_available = False
                failures.append({"item_id": item_id, "error_type": "vlm_unavailable_for_fusion"})
            constraints = default_engine().evaluate(record)
            row = {
                "item_id": item_id, "visual_record_available": visual_available,
                "record": record, "fusion_decisions": decisions,
                "constraints": [result.__dict__ | {"violations": [v.__dict__ for v in result.violations]} for result in constraints],
            }
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    elapsed = time.perf_counter() - started
    decision_counts: dict[str, int] = {}
    for row in rows:
        for decision in row["fusion_decisions"]:
            name = decision["decision"]
            decision_counts[name] = decision_counts.get(name, 0) + 1
    metrics = {
        "scope": "public unannotated B6 engineering audit; no Ground Truth accuracy claim",
        "items": len(rows),
        "items_with_schema_valid_vlm_record": sum(row["visual_record_available"] for row in rows),
        "fusion_decision_counts": decision_counts,
        "emitted_intervals": sum(len(row["record"]["intervals"]) for row in rows),
        "constraint_evaluations": sum(sum(result["evaluated_count"] for result in row["constraints"]) for row in rows),
        "constraint_violations": sum(sum(len(result["violations"]) for result in row["constraints"]) for row in rows),
        "postprocessing_latency_total_seconds": elapsed,
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "all annotations remain auto; no human-validated Ground Truth",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(row) + "\n" for row in failures), encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\nitems={len(rows)}\nvlm_available={metrics['items_with_schema_valid_vlm_record']}\nscope=audit_no_gt\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
