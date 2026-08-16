#!/usr/bin/env python3
"""Evaluate the native PDF structural expert on a frozen interval Gold manifest."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.layout import predict_native_pdf_boundaries
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return completed.stdout.strip() or None


def gold_boundaries(row: dict) -> list[float]:
    intervals = row.get("intervals")
    if intervals is None:
        intervals = json.loads(Path(row["reference_path"]).read_text(encoding="utf-8"))["stratigraphy"]["intervals"]
    return sorted({float(value) for item in intervals for value in (item["top_depth_m"], item["bottom_depth_m"])})


def metric_pair(predictions: dict[str, list[float]], gold: dict[str, list[float]]) -> dict:
    return {"boundary": boundary_metrics(predictions, gold, 0.05), "interval": interval_metrics(predictions, gold, 0.05)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--maximum-risk", type=float, default=0.55)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = load_jsonl(args.manifest)
    predictions: dict[str, list[float]] = {}
    gold = {row["record_id"]: gold_boundaries(row) for row in rows}
    diagnostics = []
    started = time.perf_counter()
    for index, row in enumerate(rows, 1):
        prediction = predict_native_pdf_boundaries(Path(row["pdf_path"]))
        predictions[row["record_id"]] = list(prediction.boundaries)
        diagnostics.append({"record_id": row["record_id"], **prediction.to_dict(), "ground_truth_tier": row.get("ground_truth_tier")})
        print(f"[{index}/{len(rows)}] {row['record_id']} status={prediction.status} boundaries={len(prediction.boundaries)}", flush=True)

    accepted = {
        row["record_id"]: predictions[row["record_id"]]
        if next(item for item in diagnostics if item["record_id"] == row["record_id"])["risk_score"] <= args.maximum_risk else []
        for row in rows
    }
    by_source = {}
    for source in sorted({str(row.get("source_family") or row.get("profile_name") or "unknown") for row in rows}):
        ids = [row["record_id"] for row in rows if str(row.get("source_family") or row.get("profile_name") or "unknown") == source]
        by_source[source] = {
            "document_count": len(ids),
            "native": metric_pair({key: predictions[key] for key in ids}, {key: gold[key] for key in ids}),
            "selective": metric_pair({key: accepted[key] for key in ids}, {key: gold[key] for key in ids}),
        }
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_native_pdf_gold_evaluation",
        "method_version": "native_pdf_semantic_and_explicit_range_v002",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "platform": platform.platform(),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "document_count": len(rows),
        "ground_truth_tier": sorted({row.get("ground_truth_tier") for row in rows}),
        "prediction_reference_conditioning": "none",
        "maximum_risk": args.maximum_risk,
        "coverage": sum(bool(predictions[row["record_id"]]) for row in rows) / max(1, len(rows)),
        "selective_coverage": sum(bool(accepted[row["record_id"]]) for row in rows) / max(1, len(rows)),
        "native": metric_pair(predictions, gold),
        "selective": metric_pair(accepted, gold),
        "by_source": by_source,
        "diagnostics": diagnostics,
        "wall_time_seconds": time.perf_counter() - started,
        "limitations": [
            "Evaluation covers interval boundaries only; lithology and descriptions are excluded.",
            "The Gold manifest is authoritative source-table agreement, not project human annotation.",
            "Native text evidence is unavailable on raster-only pages; those pages abstain.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"native": report["native"], "selective": report["selective"], "coverage": report["coverage"], "wall_time_seconds": report["wall_time_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
