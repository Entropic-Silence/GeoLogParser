#!/usr/bin/env python3
"""Evaluate a page-family-aware mixture of structural experts.

The route combines the conservative v024 page-family policy with the
reference-blind semantic-column candidate branch.  Routing is fixed from page
text/pixels and serialized candidate evidence; interval references are loaded
only after all document predictions are fixed for scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from geologparser.runtime_resources import peak_process_rss_kib
import sys
import time

import cv2

# Make the repository root importable when this file is invoked directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.layout import classify_borehole_page, extract_explicit_depth_ranges, boundaries_from_ranges
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_run_hash(source_run: Path) -> str:
    candidate = source_run / "predictions.jsonl"
    if not candidate.exists():
        candidate = source_run / "source_run_manifest.json"
    return sha256(candidate)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fold_id(record_id: str, folds: int = 5) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def references(row: dict) -> list[float]:
    return sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})


def prediction_map(report: dict, key: str) -> dict[str, list[float]]:
    output = {}
    for row in report.get("predictions", []):
        if key == "v024":
            output[row["record_id"]] = [float(value) for value in row.get("predicted_boundaries_m", [])]
        else:
            output[row["record_id"]] = [float(item["value_m"]) for item in row.get(key, [])]
    return output


def role_evidence_count(row: dict) -> int:
    count = 0
    for candidate in row.get("ranked_candidates", []):
        if any(item.get("column_role") in {"graphic_log", "core"} for item in candidate.get("provenance", [])):
            count += 1
    return count


def role_sequence_count(row: dict) -> int:
    count = 0
    for candidate in row.get("sequence_selected", []):
        if any(item.get("column_role") in {"graphic_log", "core"} for item in candidate.get("provenance", [])):
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--v024-report", type=Path, required=True)
    parser.add_argument("--role-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--evaluation-fold", type=int, default=0)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--candidate-explosion-per-page", type=int, default=1000)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    sources = load_jsonl(args.manifest)
    v024 = json.loads(args.v024_report.read_text(encoding="utf-8"))
    role = json.loads(args.role_report.read_text(encoding="utf-8"))
    baseline = prediction_map(v024, "v024")
    role_sequence = prediction_map(role, "sequence_selected")
    role_rows = {row["record_id"]: row for row in role.get("predictions", [])}
    candidate_counts = {row["record_id"]: int(row.get("candidate_count", 0)) for row in role.get("predictions", [])}
    references_by_id = {row["record_id"]: references(row) for row in sources}

    predictions: dict[str, list[float]] = {}
    diagnostics: list[dict] = []
    for source in sources:
        record_id = source["record_id"]
        pages = list(source["evaluation_pages"])
        families = []
        explicit_ranges = []
        page_details = []
        risks = []
        for page in pages:
            image_path = args.source_run / f"{record_id}_page-{page}.png"
            region_path = args.source_run / f"{record_id}_page-{page}_regions.jsonl"
            if not image_path.exists() or not region_path.exists():
                families.append("unsupported")
                risks.append("missing_page_evidence")
                continue
            rows = load_jsonl(region_path)
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                families.append("unsupported")
                risks.append("image_decode_failure")
                continue
            assessment = classify_borehole_page(rows, width=image.shape[1], height=image.shape[0])
            families.append(assessment.family)
            detail = {"page": page, "family": assessment.family, "evidence": list(assessment.evidence)}
            if assessment.family == "explicit_depth_range_table":
                ranges, range_diag = extract_explicit_depth_ranges(image_path, rows, page=page)
                explicit_ranges.extend(ranges)
                detail["range_count"] = len(ranges)
                detail["range_diagnostic"] = range_diag
                if not ranges:
                    risks.append("explicit_range_abstention")
            page_details.append(detail)

        baseline_values = baseline.get(record_id, [])
        role_values = role_sequence.get(record_id, [])
        role_row = role_rows.get(record_id, {})
        role_count = role_evidence_count(role_row)
        role_selected_count = role_sequence_count(role_row)
        candidate_count = candidate_counts.get(record_id, 0)
        candidate_per_page = candidate_count / max(1, len(pages))

        if explicit_ranges:
            predicted = boundaries_from_ranges(explicit_ranges)
            route = "explicit_range_expert"
        elif not families or any(family == "unsupported" for family in families):
            predicted = []
            route = "abstain_unsupported_family"
            risks.append("unsupported_page_family")
        elif any(family in {"scaled_composite_log", "graphical_contact_log"} for family in families) and role_selected_count >= 2:
            predicted = role_values
            route = "semantic_role_expert"
        elif baseline_values and candidate_per_page <= args.candidate_explosion_per_page:
            predicted = baseline_values
            route = "v024_baseline_expert"
        else:
            predicted = []
            route = "abstain_structural_risk"
            risks.append("candidate_explosion_or_zero_baseline")

        predictions[record_id] = predicted
        diagnostics.append({
            "record_id": record_id,
            "source_group": source.get("source_title") or record_id,
            "source_fold": fold_id(record_id, args.folds),
            "page_count": len(pages),
            "page_families": families,
            "page_details": page_details,
            "role_candidate_count": role_count,
            "role_selected_count": role_selected_count,
            "baseline_boundary_count": len(baseline_values),
            "role_boundary_count": len(role_values),
            "candidate_count": candidate_count,
            "candidate_count_per_page": candidate_per_page,
            "route": route,
            "risk_codes": sorted(set(risks)),
            "predicted_boundaries_m": predicted,
        })

    # Fixed source-disjoint development slice: no reference is consulted by
    # routing, and scoring is performed only after every prediction is fixed.
    slice_ids = {row["record_id"] for row in sources if fold_id(row["record_id"], args.folds) == args.evaluation_fold}
    all_predictions = predictions
    slice_predictions = {record_id: predictions[record_id] for record_id in slice_ids}
    slice_references = {record_id: references_by_id[record_id] for record_id in slice_ids}
    baseline_slice = {record_id: baseline.get(record_id, []) for record_id in slice_ids}
    role_slice = {record_id: role_sequence.get(record_id, []) for record_id in slice_ids}

    def metric_bundle(preds: dict[str, list[float]], refs: dict[str, list[float]]) -> dict:
        return {
            "boundary": boundary_metrics(preds, refs, 0.05),
            "interval": interval_metrics(preds, refs, 0.05),
            "document_count": len(preds),
            "reference_boundary_count": sum(len(values) for values in refs.values()),
        }

    family_metrics = {}
    for family in ("explicit_depth_range_table", "scaled_composite_log", "graphical_contact_log", "unsupported"):
        ids = [row["record_id"] for row in diagnostics if family in row["page_families"] and row["record_id"] in slice_ids]
        family_metrics[family] = metric_bundle({record_id: predictions[record_id] for record_id in ids}, {record_id: references_by_id[record_id] for record_id in ids}) if ids else {"document_count": 0}

    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_development",
        "method_version": "bgs_page_family_role_moe_v027",
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "source_run": str(args.source_run),
        "source_regions_sha256": source_run_hash(args.source_run),
        "v024_report": str(args.v024_report),
        "v024_report_sha256": sha256(args.v024_report),
        "role_report": str(args.role_report),
        "role_report_sha256": sha256(args.role_report),
        "document_count": len(sources),
        "page_count": sum(len(row["evaluation_pages"]) for row in sources),
        "evaluation_slice": {"fold": args.evaluation_fold, "folds": args.folds, "document_count": len(slice_ids), "reference_blind_routing": True},
        "overall": metric_bundle(all_predictions, references_by_id),
        "source_disjoint_slice": metric_bundle(slice_predictions, slice_references),
        "comparison": {
            "v024_baseline_overall": metric_bundle(baseline, references_by_id),
            "v024_baseline_source_disjoint_slice": metric_bundle(baseline_slice, slice_references),
            "semantic_role_overall": metric_bundle(role_sequence, references_by_id),
            "semantic_role_source_disjoint_slice": metric_bundle(role_slice, slice_references),
        },
        "family_metrics_source_disjoint_slice": family_metrics,
        "route_counts_source_disjoint_slice": {route: sum(1 for row in diagnostics if row["record_id"] in slice_ids and row["route"] == route) for route in sorted({row["route"] for row in diagnostics})},
        "route_counts_overall": {route: sum(1 for row in diagnostics if row["route"] == route) for route in sorted({row["route"] for row in diagnostics})},
        "predictions": diagnostics,
        "routing_policy": {
            "explicit_range": "explicit_range_expert",
            "scaled_or_graphical_with_role_evidence": "semantic_role_expert",
            "otherwise_supported": "v024_baseline_expert",
            "unsupported_or_structural_risk": "abstain",
            "candidate_explosion_per_page": args.candidate_explosion_per_page,
        },
        "reference_blinding": "all routing decisions fixed before references were used for scoring",
        "wall_time_seconds": time.perf_counter() - started,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "source_disjoint_slice": report["source_disjoint_slice"], "family_metrics": family_metrics, "routes": report["route_counts_source_disjoint_slice"]}, indent=2))


if __name__ == "__main__":
    main()
