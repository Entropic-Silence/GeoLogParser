#!/usr/bin/env python3
"""Compare native structural predictions with an already-frozen run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() or None


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def boundaries(intervals: list[dict]) -> list[float]:
    return sorted({float(value) for item in intervals for value in (item["top_depth_m"], item["bottom_depth_m"])})


def metric_pair(predictions: dict[str, list[float]], gold: dict[str, list[float]]) -> dict:
    return {"boundary": boundary_metrics(predictions, gold, 0.05), "interval": interval_metrics(predictions, gold, 0.05)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = load_jsonl(args.manifest)
    frozen = {row["record_id"]: row for row in load_jsonl(args.frozen_run / "predictions.jsonl")}
    native_report = json.loads(args.native_report.read_text(encoding="utf-8"))
    native = {row["record_id"]: [float(value) for value in row["boundaries"]] for row in native_report["diagnostics"]}
    gold = {row["record_id"]: boundaries(row["intervals"]) for row in rows}
    frozen_predictions = {
        "first_pass": {
            key: boundaries(row.get("first_pass_intervals", [])) for key, row in frozen.items()
        },
        "final": {
            key: boundaries(row.get("final_intervals", [])) for key, row in frozen.items()
        },
    }
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_frozen_native_comparison",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "frozen_run": str(args.frozen_run),
        "native_report": str(args.native_report),
        "native_report_sha256": sha256(args.native_report),
        "prediction_reference_conditioning": "none",
        "comparison": {
            **{name: metric_pair(predictions, gold) for name, predictions in frozen_predictions.items()},
            "native_structural": metric_pair(native, gold),
        },
        "exact_document_counts": {
            name: sum(predictions[key] == gold[key] for key in gold)
            for name, predictions in frozen_predictions.items()
        } | {"native_structural": sum(native[key] == gold[key] for key in gold)},
        "limitations": [
            "The frozen run is reused without modification; this is a descriptive comparison, not a new tuned baseline.",
            "Native structural predictions contain depth boundaries only.",
            "The manifest is authoritative source-table agreement and not project human annotation.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["comparison"], indent=2))


if __name__ == "__main__":
    main()
