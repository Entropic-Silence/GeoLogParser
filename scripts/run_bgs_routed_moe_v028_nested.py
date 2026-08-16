#!/usr/bin/env python3
"""Nested source-disjoint routing evaluation for the v027 expert mixture.

Family-to-expert choices are learned from non-target source groups only.  The
target fold is never used to decide whether the v024 baseline or semantic-role
expert is preferable for a page family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

# Make the repository root importable when this file is invoked directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fold_id(record_id: str, folds: int) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def refs(row: dict) -> list[float]:
    return sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})


def bundle(preds: dict[str, list[float]], gold: dict[str, list[float]]) -> dict:
    return {
        "boundary": boundary_metrics(preds, gold, 0.05),
        "interval": interval_metrics(preds, gold, 0.05),
        "document_count": len(preds),
        "reference_boundary_count": sum(len(values) for values in gold.values()),
    }


def doc_interval_f1(prediction: list[float], reference: list[float]) -> float:
    return float(interval_metrics({"x": prediction}, {"x": reference}, 0.05)["f1"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--v027-report", type=Path, required=True)
    parser.add_argument("--v024-report", type=Path, required=True)
    parser.add_argument("--role-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--evaluation-fold", type=int, default=0)
    parser.add_argument("--candidate-explosion-per-page", type=int, default=1000)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    manifest = load_jsonl(args.manifest)
    v027 = json.loads(args.v027_report.read_text(encoding="utf-8"))
    v024 = json.loads(args.v024_report.read_text(encoding="utf-8"))
    role = json.loads(args.role_report.read_text(encoding="utf-8"))
    gold = {row["record_id"]: refs(row) for row in manifest}
    baseline = {row["record_id"]: [float(value) for value in row.get("predicted_boundaries_m", [])] for row in v024["predictions"]}
    role_values = {row["record_id"]: [float(item["value_m"]) for item in row.get("sequence_selected", [])] for row in role["predictions"]}
    role_rows = {row["record_id"]: row for row in role["predictions"]}
    page_rows = {row["record_id"]: row for row in v027["predictions"]}

    def eligible_expert(record_id: str, expert: str) -> list[float]:
        if expert == "semantic_role":
            return role_values.get(record_id, [])
        return baseline.get(record_id, [])

    def choose_policy(train_ids: list[str]) -> dict[str, str]:
        policy: dict[str, str] = {}
        for family in ("scaled_composite_log", "graphical_contact_log"):
            ids = [record_id for record_id in train_ids if family in page_rows[record_id].get("page_families", []) and int(page_rows[record_id].get("role_selected_count", 0)) >= 2]
            if not ids:
                policy[family] = "v024_baseline"
                continue
            baseline_score = sum(doc_interval_f1(baseline.get(record_id, []), gold[record_id]) for record_id in ids) / len(ids)
            role_score = sum(doc_interval_f1(role_values.get(record_id, []), gold[record_id]) for record_id in ids) / len(ids)
            policy[family] = "semantic_role" if role_score > baseline_score else "v024_baseline"
        return policy

    predictions: dict[str, list[float]] = {}
    route_rows: list[dict] = []
    policies: dict[str, dict[str, str]] = {}
    for fold in range(args.folds):
        train_ids = [row["record_id"] for row in manifest if fold_id(row["record_id"], args.folds) != fold]
        test_ids = [row["record_id"] for row in manifest if fold_id(row["record_id"], args.folds) == fold]
        policy = choose_policy(train_ids)
        policies[str(fold)] = policy
        for record_id in test_ids:
            row = page_rows[record_id]
            families = set(row.get("page_families", []))
            baseline_values = baseline.get(record_id, [])
            role_values_row = role_values.get(record_id, [])
            role_count = int(row.get("role_selected_count", 0))
            candidate_per_page = float(row.get("candidate_count_per_page", 0.0))
            if "unsupported" in families:
                route = "abstain_unsupported_family"
                predicted = []
            elif candidate_per_page > args.candidate_explosion_per_page and not (role_count >= 2 and role_values_row):
                route = "abstain_structural_risk"
                predicted = []
            else:
                family_choices = [policy[family] for family in ("scaled_composite_log", "graphical_contact_log") if family in families]
                if role_count >= 2 and role_values_row and family_choices and all(choice == "semantic_role" for choice in family_choices):
                    route = "semantic_role_expert"
                    predicted = role_values_row
                else:
                    route = "v024_baseline_expert"
                    predicted = baseline_values
            predictions[record_id] = predicted
            route_rows.append({
                "record_id": record_id,
                "fold": fold,
                "page_families": sorted(families),
                "role_selected_count": role_count,
                "candidate_count_per_page": candidate_per_page,
                "route": route,
                "predicted_boundaries_m": predicted,
            })

    all_predictions = predictions
    slice_ids = {row["record_id"] for row in manifest if fold_id(row["record_id"], args.folds) == args.evaluation_fold}
    slice_predictions = {record_id: predictions[record_id] for record_id in slice_ids}
    slice_gold = {record_id: gold[record_id] for record_id in slice_ids}
    family_metrics = {}
    for family in ("scaled_composite_log", "graphical_contact_log", "unsupported"):
        ids = [row["record_id"] for row in route_rows if row["fold"] == args.evaluation_fold and family in row["page_families"]]
        family_metrics[family] = bundle({record_id: predictions[record_id] for record_id in ids}, {record_id: gold[record_id] for record_id in ids}) if ids else {"document_count": 0}

    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_nested_development",
        "method_version": "bgs_page_family_role_moe_v028_nested",
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "v027_report": str(args.v027_report),
        "v027_report_sha256": sha256(args.v027_report),
        "v024_report": str(args.v024_report),
        "role_report": str(args.role_report),
        "document_count": len(manifest),
        "evaluation_slice": {"fold": args.evaluation_fold, "folds": args.folds, "document_count": len(slice_ids)},
        "overall": bundle(all_predictions, gold),
        "source_disjoint_slice": bundle(slice_predictions, slice_gold),
        "family_metrics_source_disjoint_slice": family_metrics,
        "route_counts_source_disjoint_slice": {route: sum(1 for row in route_rows if row["fold"] == args.evaluation_fold and row["route"] == route) for route in sorted({row["route"] for row in route_rows})},
        "routing_policy_by_fold": policies,
        "routing_selection_metric": "mean per-document interval F1 on non-target source folds; no target-fold labels used",
        "predictions": route_rows,
        "reference_blinding": "nested family policy fit before target-fold predictions; all target predictions fixed before target references used for scoring",
        "wall_time_seconds": time.perf_counter() - started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "slice": report["source_disjoint_slice"], "family": family_metrics, "routes": report["route_counts_source_disjoint_slice"]}, indent=2))


if __name__ == "__main__":
    main()
