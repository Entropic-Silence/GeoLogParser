#!/usr/bin/env python3
"""Apply a frozen addition-only candidate-risk policy to California sequences."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import platform
import resource
import subprocess
import time
from pathlib import Path

import yaml

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest

ROOT = Path(__file__).resolve().parents[1]


def key(row: dict) -> tuple[float, float]:
    return round(float(row["top_depth_m"]), 5), round(float(row["bottom_depth_m"]), 5)


def overlaps(left: dict, right: dict) -> bool:
    return max(float(left["top_depth_m"]), float(right["top_depth_m"])) < min(
        float(left["bottom_depth_m"]), float(right["bottom_depth_m"])
    ) - 1e-9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--constraint-run", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--policy-config", type=Path, default=ROOT / "configs/experiments/paper2/california_candidate_risk_policy_v002.yaml")
    ap.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = ap.parse_args()
    policy = yaml.safe_load(args.policy_config.read_text(encoding="utf-8"))
    if not policy["rule"]["preserve_all_raw_intervals"] or not policy["rule"]["reject_if_positive_overlap_with_selected"]:
        raise ValueError("this runner requires the frozen preserve-and-nonoverlap policy")
    threshold = float(policy["rule"]["minimum_node_score"])
    tolerance = float(policy["rule"]["evaluation_tolerance_m"])
    source_run = json.loads((args.constraint_run / "run.json").read_text(encoding="utf-8"))
    source_metrics = json.loads((args.constraint_run / "metrics.json").read_text(encoding="utf-8"))
    if not source_metrics.get("reference_blinded_decision_policy"):
        raise ValueError("constraint source must have reference-blind decisions")
    rows = [json.loads(line) for line in (args.constraint_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest_ids = {json.loads(line)["record_id"] for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()}
    prediction_ids = {row["record_id"] for row in rows}
    if not prediction_ids or not prediction_ids.issubset(manifest_ids):
        raise ValueError("policy requires a non-empty constraint-run subset of the manifest")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": source_run["dataset_version"],
        "split_version": source_run["split_version"],
        "model": policy["policy_id"],
        "model_revision": "addition_only_node_score_nonoverlap_v002",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "policy_config": str(args.policy_config.relative_to(ROOT)),
            "policy_config_sha256": file_sha256(args.policy_config),
            "constraint_run_id": source_run["experiment_id"],
            "constraint_artifact_manifest_sha256": file_sha256(args.constraint_run / "artifact_manifest.json"),
            "ground_truth_sha256": file_sha256(args.manifest),
            "prediction_reference_conditioning": "none",
            "reference_blinded_decision_policy": True,
            "minimum_node_score": threshold,
            "preserve_all_raw_intervals": True,
            "reject_if_positive_overlap_with_selected": True,
        },
        "started_utc": started.isoformat(),
    })
    start = time.perf_counter()
    references, raws, selected_groups = [], [], []
    output_rows, errors = [], []
    correct_additions = incorrect_additions = accepted_documents = changed_documents = 0
    improved = unchanged = worsened = 0
    for row in rows:
        reference = row["reference_intervals"]
        raw = list(row["raw_predictions"])
        raw_keys = {key(item) for item in raw}
        proposed = [
            item for item in row["constrained_predictions"]
            if key(item) not in raw_keys
            and float(item.get("evidence", {}).get("node_score", float("-inf"))) >= threshold
        ]
        proposed.sort(key=lambda item: float(item["evidence"]["node_score"]), reverse=True)
        selected = list(raw)
        accepted, rejected = [], []
        raw_monotonic = all(
            float(right["top_depth_m"]) >= float(left["top_depth_m"])
            for left, right in zip(raw, raw[1:])
        )
        if not raw_monotonic:
            rejected.extend({"interval": item, "reason": "raw_sequence_nonmonotonic"} for item in proposed)
        else:
            for item in proposed:
                if any(overlaps(item, current) for current in selected):
                    rejected.append({"interval": item, "reason": "positive_overlap_with_selected"})
                    continue
                selected.append(item)
                accepted.append(item)
            if accepted:
                selected.sort(key=lambda item: (float(item["top_depth_m"]), float(item["bottom_depth_m"])))
        changed = bool(accepted)
        changed_documents += {key(item) for item in row["constrained_predictions"]} != raw_keys
        accepted_documents += changed
        for item in accepted:
            is_correct = any(
                abs(float(item["top_depth_m"]) - float(target["top_depth_m"])) <= tolerance
                and abs(float(item["bottom_depth_m"]) - float(target["bottom_depth_m"])) <= tolerance
                for target in reference
            )
            correct_additions += is_correct
            incorrect_additions += not is_correct
        raw_matches = len(match_intervals_by_boundaries(reference, raw, tolerance_m=tolerance)[0])
        selected_matches, missing, extra = match_intervals_by_boundaries(reference, selected, tolerance_m=tolerance)
        delta = len(selected_matches) - raw_matches
        improved += delta > 0
        worsened += delta < 0
        unchanged += delta == 0
        references.append(reference)
        raws.append(raw)
        selected_groups.append(selected)
        output_rows.append({
            "record_id": row["record_id"],
            "county": row.get("county"),
            "decision": "ACCEPT_HIGH_CONFIDENCE_ADDITIONS" if accepted else "RETAIN_RAW_ABSTAIN_CORRECTION",
            "decision_inputs": {
                "raw_prediction_count": len(raw),
                "constrained_prediction_count": len(row["constrained_predictions"]),
                "threshold_eligible_addition_count": len(proposed),
                "accepted_addition_count": len(accepted),
                "overlap_rejected_addition_count": len(rejected),
                "raw_sequence_monotonic": raw_monotonic,
            },
            "accepted_additions": accepted,
            "rejected_additions": rejected,
            "reference_intervals": reference,
            "raw_predictions": raw,
            "risk_selected_predictions": selected,
            "raw_match_count": raw_matches,
            "risk_selected_match_count": len(selected_matches),
            "match_delta": delta,
            "unmatched_reference_indices": missing,
            "unmatched_prediction_indices": extra,
        })
        errors.extend({"record_id": row["record_id"], "error_type": "missing_interval_after_candidate_risk_policy", "reference_index": index} for index in missing)
        errors.extend({"record_id": row["record_id"], "error_type": "spurious_interval_after_candidate_risk_policy", "prediction_index": index} for index in extra)
    raw_metrics = boundary_matched_interval_metrics(references, raws, tolerance_m=tolerance)
    selected_metrics = boundary_matched_interval_metrics(references, selected_groups, tolerance_m=tolerance)
    actions = correct_additions + incorrect_additions
    metrics = {
        "scope": "published-manual-transcription Gold benchmark evaluation",
        "comparison": "raw_vs_addition_only_candidate_risk_policy",
        "reference_ground_truth_tier": source_metrics["reference_ground_truth_tier"],
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "policy_id": policy["policy_id"],
        "document_count": len(rows),
        "reference_interval_count": sum(map(len, references)),
        "changed_document_count": changed_documents,
        "accepted_correction_document_count": accepted_documents,
        "correction_coverage": {"value": accepted_documents / changed_documents if changed_documents else None, "numerator": accepted_documents, "denominator": changed_documents},
        "document_outcomes": {"improved": improved, "unchanged": unchanged, "worsened": worsened},
        "raw_interval_metrics": {name: value.to_dict() for name, value in raw_metrics.items()},
        "risk_selected_interval_metrics": {name: value.to_dict() for name, value in selected_metrics.items()},
        "accepted_correct_additions": correct_additions,
        "accepted_incorrect_additions": incorrect_additions,
        "accepted_correction_actions": actions,
        "false_correction_rate": {"value": incorrect_additions / actions if actions else None, "numerator": incorrect_additions, "denominator": actions, "definition": "incorrect accepted additions / all accepted additions"},
        "wall_time_seconds": time.perf_counter() - start,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (run / "predictions.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in output_rows), encoding="utf-8")
    (run / "errors.jsonl").write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in errors), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"started_utc={started.isoformat()}\npolicy={policy['policy_id']}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
