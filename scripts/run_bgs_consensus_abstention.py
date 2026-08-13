#!/usr/bin/env python3
"""Evaluate a two-reader consensus/abstention policy on BGS metadata.

This consumes two already completed, immutable first-pass runs on the same
authoritative-metadata manifest.  It never reads reference values to make an
accept/review decision; references are used only after decisions are frozen to
score coverage, accepted accuracy, and manual-review recall.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import date
from pathlib import Path

from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESSERACT = ROOT / "results/2026-08-13/P1_METADATA_BGS_TESSERACT_FORMAL_004"
DEFAULT_RAPIDOCR = ROOT / "results/2026-08-13/P1_METADATA_BGS_RAPIDOCR_FORMAL_001"
DEFAULT_MANIFEST = Path(
    "/data/GeoLogParser/datasets/public/bgs_authoritative_metadata_v001/metadata/manifest.jsonl"
)
FIELDS = ("borehole_id", "x_coordinate", "y_coordinate", "final_depth_m")


def _rows(path: Path) -> dict[str, dict]:
    return {
        row["source_record_id"]: row
        for row in (
            json.loads(line) for line in (path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def _equal(a, b, tolerance: float) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tolerance
    return str(a) == str(b)


def _score(field_rows: list[dict]) -> dict:
    reference_rows = [row for row in field_rows if row["expected"] is not None]
    accepted = [row for row in reference_rows if row["decision"] == "ACCEPT_CONSENSUS"]
    reviewed = [row for row in reference_rows if row["decision"] == "NEEDS_REVIEW"]
    accepted_correct = sum(row["accepted_correct"] for row in accepted)
    total_errors = sum(not row["accepted_correct"] for row in accepted) + sum(row["review_needed"] for row in reviewed)
    caught_errors = sum(row["review_needed"] for row in reviewed)
    return {
        "reference_count": len(reference_rows),
        "accepted_count": len(accepted),
        "review_count": len(reviewed),
        "coverage": len(accepted) / len(reference_rows) if reference_rows else None,
        "accepted_accuracy": accepted_correct / len(accepted) if accepted else None,
        "accepted_error_count": len(accepted) - accepted_correct,
        "review_needed_count": sum(row["review_needed"] for row in reviewed),
        "manual_review_recall": caught_errors / total_errors if total_errors else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="P2_BGS_METADATA_CONSENSUS_ABSTENTION_001")
    parser.add_argument("--tesseract-run", type=Path, default=DEFAULT_TESSERACT)
    parser.add_argument("--rapidocr-run", type=Path, default=DEFAULT_RAPIDOCR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--numeric-tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    started = time.perf_counter()
    tesseract = _rows(args.tesseract_run)
    rapidocr = _rows(args.rapidocr_run)
    source_ids = sorted(set(tesseract) & set(rapidocr), key=lambda value: int(value))
    if len(source_ids) != len(tesseract) or len(source_ids) != len(rapidocr):
        raise ValueError("input first-pass runs do not contain identical source IDs")
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": "bgs_authoritative_metadata_v001_downloaded31",
        "split_version": "same_source_consensus_abstention_v001",
        "model": "tesseract_rapidocr_exact_consensus_abstention",
        "model_revision": "decision_policy_v001",
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "ground_truth_sha256": file_sha256(args.manifest),
            "ground_truth_tier": "AUTHORITATIVE_METADATA",
            "decision_blinding": "references not consulted until after accept/review decisions",
            "accept_rule": "both independent first-pass readers emit the same non-null value",
            "numeric_tolerance": args.numeric_tolerance,
            "tesseract_run": str(args.tesseract_run.resolve()),
            "tesseract_run_sha256": file_sha256(args.tesseract_run / "run.json"),
            "tesseract_predictions_sha256": file_sha256(args.tesseract_run / "predictions.jsonl"),
            "rapidocr_run": str(args.rapidocr_run.resolve()),
            "rapidocr_run_sha256": file_sha256(args.rapidocr_run / "run.json"),
            "rapidocr_predictions_sha256": file_sha256(args.rapidocr_run / "predictions.jsonl"),
            "scope": "real authoritative-metadata consensus/abstention study; no interval/lithology reference",
        },
    })

    decisions: list[dict] = []
    for source_id in source_ids:
        left, right = tesseract[source_id], rapidocr[source_id]
        if left["expected"] != right["expected"]:
            raise ValueError(f"reference mismatch for source {source_id}")
        for field in FIELDS:
            expected = left["expected"][field]
            left_value = left["predicted"][field]
            right_value = right["predicted"][field]
            accept = _equal(left_value, right_value, args.numeric_tolerance)
            accepted_value = left_value if accept else None
            accepted_correct = accept and _equal(accepted_value, expected, args.numeric_tolerance)
            review_needed = (not accept) and expected is not None and not (
                _equal(left_value, expected, args.numeric_tolerance)
                and _equal(right_value, expected, args.numeric_tolerance)
            )
            decisions.append({
                "source_record_id": source_id,
                "field": field,
                "tesseract_value": left_value,
                "rapidocr_value": right_value,
                "decision": "ACCEPT_CONSENSUS" if accept else "NEEDS_REVIEW",
                "accepted_value": accepted_value,
                "expected": expected,
                "accepted_correct": bool(accepted_correct),
                "review_needed": bool(review_needed),
            })

    by_field = {field: _score([row for row in decisions if row["field"] == field]) for field in FIELDS}
    all_score = _score(decisions)
    elapsed = time.perf_counter() - started
    metrics = {
        "scope": "authoritative-metadata consensus/abstention evaluation",
        "reference_ground_truth_tier": "AUTHORITATIVE_METADATA",
        "document_count": len(source_ids),
        "field_decision_count": len(decisions),
        "interval_ground_truth_available": False,
        "decision_policy": "exact non-null cross-reader consensus else NEEDS_REVIEW",
        "by_field": by_field,
        "overall": all_score,
        "latency_seconds_policy_only": elapsed,
        "source_first_pass_latency_excluded": True,
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in decisions), encoding="utf-8",
    )
    errors = [row for row in decisions if (row["decision"] == "ACCEPT_CONSENSUS" and not row["accepted_correct"])]
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in errors), encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"status=completed\ndocuments={len(source_ids)}\nfield_decisions={len(decisions)}\n"
        f"accepted={all_score['accepted_count']}\nreview={all_score['review_count']}\n"
        f"latency_seconds_policy_only={elapsed:.9f}\n",
        encoding="utf-8",
    )
    print(run)


if __name__ == "__main__":
    main()
