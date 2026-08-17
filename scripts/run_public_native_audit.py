#!/usr/bin/env python3
"""Run direct-PDF text + conservative extraction on an unannotated manifest."""

from __future__ import annotations

import argparse
import json
import platform
from geologparser.runtime_resources import peak_process_rss_kib
import subprocess
import time
from pathlib import Path

from geologparser.constraints import load_engine_config
from geologparser.experiment import create_run_directory
from geologparser.pipeline import run_minimal_baseline
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONSTRAINT_CONFIG = ROOT / "configs/constraints/default_v001.yaml"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--constraint-config", type=Path, default=DEFAULT_CONSTRAINT_CONFIG)
    arguments = parser.parse_args()
    constraint_engine = load_engine_config(arguments.constraint_config)
    manifest = [json.loads(line) for line in arguments.manifest.read_text(encoding="utf-8").splitlines() if line]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": "2026-08-12",
        "dataset_version": arguments.dataset_version,
        "split_version": "engineering_audit_no_training_no_ground_truth",
        "model": "direct_pdf_text_conservative_regex",
        "model_revision": "geologparser_native_pdf_v001",
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "manifest_path": str(arguments.manifest),
            "constraint_tolerance_m": "0.05",
            "constraint_config_path": str(arguments.constraint_config.resolve()),
            "constraint_config_sha256": file_sha256(arguments.constraint_config),
            "scope": "public unannotated engineering audit; no accuracy claim",
        },
    })
    rows = []
    started = time.perf_counter()
    with (run / "predictions.jsonl").open("w", encoding="utf-8") as stream:
        for item in manifest:
            source = Path(item["local_path"])
            item_started = time.perf_counter()
            regions, record = run_minimal_baseline(source, ocr_language="eng")
            constraints = constraint_engine.evaluate(record)
            row = {
                "source_record_id": item["source_record_id"],
                "source_sha256": item["sha256"],
                "page_count": item["page_count"],
                "latency_seconds": time.perf_counter() - item_started,
                "text_region_count": len(regions),
                "interval_count": len(record["intervals"]),
                "record": record,
                "constraints": [
                    result.__dict__ | {"violations": [violation.__dict__ for violation in result.violations]}
                    for result in constraints
                ],
            }
            rows.append(row)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    elapsed = time.perf_counter() - started
    metrics = {
        "scope": "public unannotated engineering audit; no accuracy claim",
        "documents": len(rows),
        "pages": sum(row["page_count"] for row in rows),
        "documents_with_borehole_id": sum(row["record"]["borehole"]["borehole_id"]["value"] is not None for row in rows),
        "documents_with_final_depth": sum(row["record"]["borehole"]["final_depth_m"]["value"] is not None for row in rows),
        "documents_with_any_interval": sum(row["interval_count"] > 0 for row in rows),
        "emitted_intervals": sum(row["interval_count"] for row in rows),
        "constraint_evaluations": sum(sum(x["evaluated_count"] for x in row["constraints"]) for row in rows),
        "constraint_violations": sum(sum(len(x["violations"]) for x in row["constraints"]) for row in rows),
        "latency_total_seconds": elapsed,
        "latency_seconds_per_page": elapsed / sum(row["page_count"] for row in rows),
        "peak_process_rss_kib": peak_process_rss_kib(),
        "accuracy_metrics": None,
        "accuracy_metrics_reason": "dataset has no project human Ground Truth yet",
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "run.log").write_text(
        f"status=completed\ndocuments={len(rows)}\npages={metrics['pages']}\nscope=public_unannotated_audit\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
