#!/usr/bin/env python3
"""Fit a development-only confidence lookup and evaluate selective coverage.

This is a secondary, descriptive analysis.  It combines the frozen v2
constraint/rereading decisions with an independently executed RapidOCR path.
The lookup is fit only on the development partition and then applied without
access to held-out references.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import math
import platform
import subprocess
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def indexed(rows: list[dict]) -> dict[str, dict]:
    result = {str(row["record_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate record_id in prediction file")
    return result


def signature(method_row: dict, peer_row: dict) -> str:
    agreement = method_row["final_intervals"] == peer_row["predicted_intervals"]
    triggered = bool(method_row.get("triggers"))
    return "|".join((method_row["decision"], f"trigger={int(triggered)}", f"peer_exact={int(agreement)}"))


def brier_score(labels: list[int], probabilities: list[float]) -> float:
    return sum((probability - label) ** 2 for label, probability in zip(labels, probabilities)) / len(labels)


def negative_log_likelihood(labels: list[int], probabilities: list[float]) -> float:
    epsilon = 1e-12
    return -sum(
        label * math.log(min(1 - epsilon, max(epsilon, probability)))
        + (1 - label) * math.log(min(1 - epsilon, max(epsilon, 1 - probability)))
        for label, probability in zip(labels, probabilities)
    ) / len(labels)


def fixed_bin_calibration(labels: list[int], probabilities: list[float], bins: int = 5) -> tuple[float, list[dict]]:
    rows = []
    total = len(labels)
    ece = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            (label, probability)
            for label, probability in zip(labels, probabilities)
            if lower <= probability <= upper and (index == bins - 1 or probability < upper)
        ]
        if not members:
            continue
        accuracy = sum(item[0] for item in members) / len(members)
        mean_confidence = sum(item[1] for item in members) / len(members)
        gap = abs(accuracy - mean_confidence)
        ece += len(members) / total * gap
        rows.append({
            "lower": lower,
            "upper": upper,
            "count": len(members),
            "accuracy": accuracy,
            "mean_confidence": mean_confidence,
            "absolute_gap": gap,
        })
    return ece, rows


def interval_metrics(rows: list[dict]) -> dict:
    references = [row["reference_intervals"] for row in rows]
    predictions = [row["final_intervals"] for row in rows]
    return {
        name: metric.to_dict()
        for name, metric in boundary_matched_interval_metrics(
            references, predictions, tolerance_m=0.05,
        ).items()
    }


def policy_metrics(rows: list[dict], accepted_ids: set[str]) -> dict:
    accepted = [row for row in rows if row["record_id"] in accepted_ids]
    exact = sum(bool(row["final_exact"]) for row in accepted)
    return {
        "accepted_documents": len(accepted),
        "total_documents": len(rows),
        "coverage": len(accepted) / len(rows),
        "document_exact": {
            "numerator": exact,
            "denominator": len(accepted),
            "value": exact / len(accepted) if accepted else None,
        },
        "interval_metrics": interval_metrics(accepted) if accepted else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--development-method-run", type=Path, required=True)
    parser.add_argument("--development-peer-run", type=Path, required=True)
    parser.add_argument("--heldout-method-run", type=Path, required=True)
    parser.add_argument("--heldout-peer-run", type=Path, required=True)
    parser.add_argument("--development-manifest", type=Path, required=True)
    parser.add_argument("--heldout-manifest", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    dev_method = indexed(read_rows(args.development_method_run / "predictions.jsonl"))
    dev_peer = indexed(read_rows(args.development_peer_run / "predictions.jsonl"))
    held_method = indexed(read_rows(args.heldout_method_run / "predictions.jsonl"))
    held_peer = indexed(read_rows(args.heldout_peer_run / "predictions.jsonl"))
    if set(dev_method) != set(dev_peer) or set(held_method) != set(held_peer):
        raise ValueError("method/peer record sets differ")
    if set(dev_method) & set(held_method):
        raise ValueError("development and held-out records overlap")

    # Uniform Beta(1, 1) smoothing makes every fitted probability finite and
    # records the small-sample uncertainty without test-set fitting.
    fitted: dict[str, dict] = {}
    for record_id, row in dev_method.items():
        key = signature(row, dev_peer[record_id])
        bucket = fitted.setdefault(key, {"documents": 0, "correct": 0})
        bucket["documents"] += 1
        bucket["correct"] += int(bool(row["final_exact"]))
    for bucket in fitted.values():
        bucket["probability"] = (bucket["correct"] + 1) / (bucket["documents"] + 2)

    prediction_rows = []
    for record_id in sorted(held_method):
        row = held_method[record_id]
        key = signature(row, held_peer[record_id])
        if key not in fitted:
            raise ValueError(f"held-out signature absent from development lookup: {key}")
        prediction_rows.append({
            "record_id": record_id,
            "signature": key,
            "confidence": fitted[key]["probability"],
            "correct": bool(row["final_exact"]),
            "decision": row["decision"],
            "triggers": row.get("triggers", []),
            "peer_exact_agreement": row["final_intervals"] == held_peer[record_id]["predicted_intervals"],
            "reference_intervals": row["reference_intervals"],
            "final_intervals": row["final_intervals"],
            "final_exact": bool(row["final_exact"]),
        })

    labels = [int(row["correct"]) for row in prediction_rows]
    probabilities = [float(row["confidence"]) for row in prediction_rows]
    ece, calibration_bins = fixed_bin_calibration(labels, probabilities)

    threshold_rows = []
    for threshold in sorted(set(probabilities), reverse=True):
        accepted_ids = {
            row["record_id"] for row in prediction_rows if row["confidence"] >= threshold
        }
        threshold_rows.append({
            "threshold": threshold,
            **policy_metrics(prediction_rows, accepted_ids),
        })

    policies = {
        "accept_all": policy_metrics(prediction_rows, set(held_method)),
        "abstain_needs_review": policy_metrics(
            prediction_rows,
            {row["record_id"] for row in prediction_rows if row["decision"] != "NEEDS_REVIEW"},
        ),
        "require_peer_exact_agreement": policy_metrics(
            prediction_rows,
            {row["record_id"] for row in prediction_rows if row["peer_exact_agreement"]},
        ),
        "require_peer_exact_and_no_review": policy_metrics(
            prediction_rows,
            {
                row["record_id"] for row in prediction_rows
                if row["peer_exact_agreement"] and row["decision"] != "NEEDS_REVIEW"
            },
        ),
    }

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": "swissgeol_thurgau_paired_v003_authoritative_interval",
        "split_version": "v003_content_group_development_fit__heldout_evaluation",
        "model": "v2_reread_plus_rapidocr_development_fitted_selective_confidence",
        "model_revision": "beta_smoothed_signature_lookup_v001",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "development_manifest_sha256": file_sha256(args.development_manifest),
            "ground_truth_sha256": file_sha256(args.heldout_manifest),
            "development_method_predictions_sha256": file_sha256(args.development_method_run / "predictions.jsonl"),
            "development_peer_predictions_sha256": file_sha256(args.development_peer_run / "predictions.jsonl"),
            "heldout_method_predictions_sha256": file_sha256(args.heldout_method_run / "predictions.jsonl"),
            "heldout_peer_predictions_sha256": file_sha256(args.heldout_peer_run / "predictions.jsonl"),
            "confidence_features": ["decision", "trigger_presence", "cross_backend_exact_agreement"],
            "calibration": "development empirical exact-document rate with Beta(1,1) smoothing",
            "evaluation_role": "secondary_descriptive_post_result_calibration",
        },
        "started_utc": started.isoformat(),
    })
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in prediction_rows),
        encoding="utf-8",
    )
    metrics = {
        "scope": "authoritative-interval selective-confidence secondary analysis",
        "evaluation_role": "secondary_descriptive_post_result_calibration",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "development_document_count": len(dev_method),
        "heldout_document_count": len(held_method),
        "development_heldout_overlap_count": 0,
        "fitted_lookup": fitted,
        "brier_score": brier_score(labels, probabilities),
        "negative_log_likelihood": negative_log_likelihood(labels, probabilities),
        "expected_calibration_error_5_bin": ece,
        "calibration_bins": calibration_bins,
        "coverage_accuracy_curve": threshold_rows,
        "operational_policies": policies,
        "limitations": [
            "secondary analysis specified after the primary held-out method result was observed",
            "only 37 development and 35 held-out documents",
            "document exactness is stricter than field-level calibration but yields a small denominator",
            "source-agreement-selected interval tables are not a representative cross-source sample",
        ],
    }
    (run / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    errors = [
        {"record_id": row["record_id"], "error_type": "document_not_exact", "confidence": row["confidence"], "signature": row["signature"]}
        for row in prediction_rows if not row["correct"]
    ]
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in errors), encoding="utf-8",
    )
    ended = datetime.now(timezone.utc)
    (run / "run.log").write_text(
        "\n".join((
            f"started_utc={started.isoformat()}",
            f"ended_utc={ended.isoformat()}",
            f"development_documents={len(dev_method)}",
            f"heldout_documents={len(held_method)}",
            "status=completed",
            "",
        )),
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
