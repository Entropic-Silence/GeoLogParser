#!/usr/bin/env python3
"""Apply a frozen reference-blind document-level California correction policy."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import platform
from geologparser.runtime_resources import peak_process_rss_kib
import subprocess
import time
from pathlib import Path

import yaml

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]


def boundary_set(rows: list[dict]) -> set[tuple[float, float]]:
    return {
        (round(float(row["top_depth_m"]), 5), round(float(row["bottom_depth_m"]), 5))
        for row in rows
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--constraint-run", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--policy-config",
        type=Path,
        default=ROOT / "configs/experiments/paper2/california_selective_policy_v001.yaml",
    )
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    policy = yaml.safe_load(args.policy_config.read_text(encoding="utf-8"))
    expected = "constrained_prediction_count > raw_prediction_count"
    if policy["rule"]["accept_constrained_if"] != expected:
        raise ValueError(f"unsupported frozen policy: {policy['rule']['accept_constrained_if']}")
    source_run = json.loads((args.constraint_run / "run.json").read_text(encoding="utf-8"))
    source_metrics = json.loads((args.constraint_run / "metrics.json").read_text(encoding="utf-8"))
    if not source_metrics.get("reference_blinded_decision_policy"):
        raise ValueError("source constraint decisions are not reference-blind")
    rows = [
        json.loads(line)
        for line in (args.constraint_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest_ids = {
        json.loads(line)["record_id"]
        for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    prediction_ids = {row["record_id"] for row in rows}
    if not prediction_ids or not prediction_ids.issubset(manifest_ids):
        raise ValueError("constraint prediction IDs are not a non-empty manifest subset")

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    started = datetime.now(timezone.utc)
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": source_run["dataset_version"],
        "split_version": source_run["split_version"],
        "model": policy["policy_id"],
        "model_revision": "document_net_expansion_rule_v001",
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
            "decision_rule": expected,
        },
        "started_utc": started.isoformat(),
    })
    wall_started = time.perf_counter()
    reference_groups, raw_groups, constrained_groups, selective_groups = [], [], [], []
    output_rows, errors = [], []
    totals = {
        "raw_correct_kept": 0,
        "raw_correct_removed": 0,
        "raw_incorrect_removed": 0,
        "constrained_correct_added": 0,
        "constrained_incorrect_added": 0,
    }
    changed_documents = accepted_documents = improved = unchanged = worsened = 0
    for row in rows:
        references = row["reference_intervals"]
        raw = row["raw_predictions"]
        constrained = row["constrained_predictions"]
        changed = boundary_set(raw) != boundary_set(constrained)
        accept = changed and len(constrained) > len(raw)
        selected = constrained if accept else raw
        if changed:
            changed_documents += 1
        if accept:
            accepted_documents += 1
            for key, value in row["correction_taxonomy"].items():
                totals[key] += int(value)
        raw_matches, _, _ = match_intervals_by_boundaries(references, raw, tolerance_m=0.05)
        selected_matches, missing, extra = match_intervals_by_boundaries(
            references, selected, tolerance_m=0.05
        )
        delta = len(selected_matches) - len(raw_matches)
        if delta > 0:
            improved += 1
        elif delta < 0:
            worsened += 1
        else:
            unchanged += 1
        reference_groups.append(references)
        raw_groups.append(raw)
        constrained_groups.append(constrained)
        selective_groups.append(selected)
        output_rows.append({
            "record_id": row["record_id"],
            "county": row.get("county"),
            "decision": "ACCEPT_CONSTRAINED" if accept else (
                "RETAIN_RAW_ABSTAIN_CORRECTION" if changed else "NO_CORRECTION_PROPOSED"
            ),
            "decision_inputs": {
                "raw_prediction_count": len(raw),
                "constrained_prediction_count": len(constrained),
            },
            "reference_intervals": references,
            "raw_predictions": raw,
            "unconstrained_correction_predictions": constrained,
            "selective_predictions": selected,
            "raw_match_count": len(raw_matches),
            "selective_match_count": len(selected_matches),
            "match_delta": delta,
            "unmatched_reference_indices": missing,
            "unmatched_selective_indices": extra,
        })
        errors.extend(
            {"record_id": row["record_id"], "error_type": "missing_interval_after_selective_policy", "reference_index": value}
            for value in missing
        )
        errors.extend(
            {"record_id": row["record_id"], "error_type": "spurious_interval_after_selective_policy", "prediction_index": value}
            for value in extra
        )

    raw_metrics = boundary_matched_interval_metrics(reference_groups, raw_groups, tolerance_m=0.05)
    constrained_metrics = boundary_matched_interval_metrics(
        reference_groups, constrained_groups, tolerance_m=0.05
    )
    selective_metrics = boundary_matched_interval_metrics(
        reference_groups, selective_groups, tolerance_m=0.05
    )
    actions = sum(
        totals[key]
        for key in (
            "raw_correct_removed", "raw_incorrect_removed",
            "constrained_correct_added", "constrained_incorrect_added",
        )
    )
    harmful = totals["raw_correct_removed"] + totals["constrained_incorrect_added"]
    metrics = {
        "scope": "human-GT benchmark evaluation",
        "comparison": "raw_vs_unselective_constraint_vs_selective_constraint",
        "reference_ground_truth_tier": source_metrics["reference_ground_truth_tier"],
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "policy_id": policy["policy_id"],
        "document_count": len(rows),
        "reference_interval_count": sum(len(group) for group in reference_groups),
        "changed_document_count": changed_documents,
        "accepted_correction_document_count": accepted_documents,
        "correction_coverage": {
            "value": accepted_documents / changed_documents if changed_documents else None,
            "numerator": accepted_documents,
            "denominator": changed_documents,
        },
        "retained_or_unchanged_document_count": len(rows) - accepted_documents,
        "document_outcomes": {
            "improved": improved,
            "unchanged": unchanged,
            "worsened": worsened,
        },
        "raw_interval_metrics": {name: value.to_dict() for name, value in raw_metrics.items()},
        "unselective_constraint_interval_metrics": {
            name: value.to_dict() for name, value in constrained_metrics.items()
        },
        "selective_interval_metrics": {
            name: value.to_dict() for name, value in selective_metrics.items()
        },
        "accepted_correction_taxonomy": totals,
        "accepted_correction_actions": actions,
        "harmful_accepted_correction_actions": harmful,
        "selective_false_correction_rate": {
            "value": harmful / actions if actions else None,
            "numerator": harmful,
            "denominator": actions,
            "definition": "harmful boundary actions / all accepted changed-boundary actions",
        },
        "wall_time_seconds": time.perf_counter() - wall_started,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output_rows),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in errors),
        encoding="utf-8",
    )
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"started_utc={started.isoformat()}\nconstraint_run={source_run['experiment_id']}\npolicy={policy['policy_id']}\nstatus=completed\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
