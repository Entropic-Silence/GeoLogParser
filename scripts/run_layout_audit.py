#!/usr/bin/env python3
"""Run B3 positioned-text layout rules on a public unannotated page manifest."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from pathlib import Path

from geologparser.constraints import default_engine
from geologparser.experiment import create_run_directory
from geologparser.extraction import extract_structured
from geologparser.layout import extract_depth_column_intervals
from geologparser.pdf import PyMuPDFPanelTextAdapter


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    items = [json.loads(line) for line in arguments.manifest.read_text(encoding="utf-8").splitlines() if line]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id, "git_commit": commit, "date": "2026-08-12",
        "dataset_version": arguments.dataset_version,
        "split_version": "engineering_audit_no_training_no_ground_truth",
        "model": "B3_native_positioned_text_depth_column_rules",
        "model_revision": "depth_column_layout_v001", "prompt_version": "not_applicable", "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "manifest_path": str(arguments.manifest), "x_bin_points": 12.0,
            "minimum_unique_ranges": 3,
            "scope": "public auto-proposal B3 engineering audit; no accuracy claim",
        },
    })
    adapter = PyMuPDFPanelTextAdapter()
    rows = []
    started = time.perf_counter()
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for item in items:
            item_started = time.perf_counter()
            regions = adapter.extract_panel(
                Path(item["source_path"]), int(item["source_page"]), tuple(item["normalized_bbox"]),
            )
            record = extract_structured(regions, Path(item["source_path"]))
            record["document"]["document_id"] = item["panel_id"]
            record["document"]["page_count"] = 1
            record["document"]["metadata"].update({
                "project_id": item.get("project_id"), "template_id": item.get("template_id"),
                "source_id": arguments.dataset_version,
            })
            intervals = extract_depth_column_intervals(regions)
            record["intervals"] = intervals
            constraints = default_engine().evaluate(record)
            row = {
                "item_id": item["panel_id"], "text_region_count": len(regions),
                "interval_count": len(intervals), "record": record,
                "constraints": [result.__dict__ | {"violations": [v.__dict__ for v in result.violations]} for result in constraints],
                "latency_seconds": time.perf_counter() - item_started,
            }
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    elapsed = time.perf_counter() - started
    metrics = {
        "scope": "public auto-proposal B3 engineering audit; no Ground Truth accuracy claim",
        "items": len(rows), "items_with_any_interval": sum(row["interval_count"] > 0 for row in rows),
        "emitted_intervals": sum(row["interval_count"] for row in rows),
        "constraint_evaluations": sum(sum(x["evaluated_count"] for x in row["constraints"]) for row in rows),
        "constraint_violations": sum(sum(len(x["violations"]) for x in row["constraints"]) for row in rows),
        "latency_total_seconds": elapsed, "latency_mean_seconds_per_page": elapsed / len(rows),
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "all source proposals remain auto; no human-validated Ground Truth",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\nitems={len(rows)}\nitems_with_intervals={metrics['items_with_any_interval']}\nscope=audit_no_gt\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
