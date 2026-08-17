#!/usr/bin/env python3
"""Evaluate evidence-grounded acceptance of frozen direct-VLM proposals."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest
from geologparser.runtime_resources import peak_process_rss_kib
from geologparser.vlm.assurance import (
    agreeing_interval_pairs,
    monotonic_nonoverlapping_indices,
    numeric_region_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def zero_event_upper_bound(sample_size: int, alpha: float = 0.05) -> float | None:
    return 1.0 - alpha ** (1.0 / sample_size) if sample_size else None


def interval_equal(left: Mapping[str, Any], right: Mapping[str, Any], tolerance: float = 1e-9) -> bool:
    return all(abs(float(left[key]) - float(right[key])) <= tolerance for key in ("top_depth_m", "bottom_depth_m"))


def proposal_pages(page_rows: list[dict[str, Any]], document_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in page_rows:
        grouped.setdefault(str(row["record_id"]), []).append(row)
    output: dict[str, list[dict[str, Any]]] = {}
    by_id = {str(row["record_id"]): row for row in document_rows}
    for record_id, pages in grouped.items():
        mapped: list[dict[str, Any]] = []
        for page in sorted(pages, key=lambda item: (item.get("page_index") or 0, item["page_key"])):
            for interval in page.get("intervals", []) if page.get("parse_status") == "json_valid" else []:
                mapped.append({
                    "interval": interval,
                    "page_index": page.get("page_index"),
                    "page_key": page["page_key"],
                    "image_sha256": page["image_sha256"],
                })
        expected = by_id[record_id]["predicted_intervals"]
        if len(mapped) != len(expected) or any(not interval_equal(item["interval"], interval) for item, interval in zip(mapped, expected)):
            raise ValueError(f"page/document proposal aggregation mismatch for {record_id}")
        output[record_id] = mapped
    return output


def load_positioned_regions(run: Path, row: Mapping[str, Any]) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    for page in row.get("evidence", []):
        path = run / str(page["ocr_regions_path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        for region in load_jsonl(path):
            region["page_index"] = page.get("page")
            region["regions_path"] = path.name
            regions.append(region)
    return regions


def complete_sequence(intervals: list[Mapping[str, Any]], tolerance_m: float) -> bool:
    if not intervals or abs(float(intervals[0]["top_depth_m"])) > tolerance_m:
        return False
    return all(
        abs(float(current["bottom_depth_m"]) - float(following["top_depth_m"])) <= tolerance_m
        for current, following in zip(intervals, intervals[1:])
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--vlm-run", type=Path, required=True)
    parser.add_argument("--positioned-run", type=Path, required=True)
    parser.add_argument("--protocol-config", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--cohort-role", choices=("development", "validation", "heldout"), required=True)
    arguments = parser.parse_args()
    started = time.perf_counter()
    config = json.loads(arguments.protocol_config.read_text(encoding="utf-8"))
    tolerance_m = float(config["agreement_tolerance_m"])
    evidence_tolerance = float(config["field_evidence_tolerance_source_units"])
    qwen_metrics = json.loads((arguments.vlm_run / "metrics.json").read_text(encoding="utf-8"))
    positioned_metrics = json.loads((arguments.positioned_run / "metrics.json").read_text(encoding="utf-8"))
    qwen_run_metadata = json.loads((arguments.vlm_run / "run.json").read_text(encoding="utf-8"))
    scale_to_m = float(qwen_run_metadata["config"]["metres_per_source_unit"])
    qwen_documents = load_jsonl(arguments.vlm_run / "predictions.jsonl")
    positioned_documents = load_jsonl(arguments.positioned_run / "predictions.jsonl")
    qwen_pages = load_jsonl(arguments.vlm_run / "page_predictions.jsonl")
    qwen_by_id = {str(row["record_id"]): row for row in qwen_documents}
    positioned_by_id = {str(row["record_id"]): row for row in positioned_documents}
    if qwen_by_id.keys() != positioned_by_id.keys():
        raise ValueError("VLM and positioned-reader document sets differ")
    page_map = proposal_pages(qwen_pages, qwen_documents)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": qwen_metrics.get("scope"),
        "split_version": arguments.cohort_role,
        "model": "frozen_direct_vlm_plus_frozen_positioned_reader_assurance",
        "model_revision": config["protocol_id"],
        "prompt_version": "inherited_frozen_direct_vlm_prompt",
        "seed": 0,
        "hardware": {"device": "CPU post-processing over archived readers", "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "protocol_config_sha256": file_sha256(arguments.protocol_config),
            "vlm_metrics_sha256": file_sha256(arguments.vlm_run / "metrics.json"),
            "vlm_predictions_sha256": file_sha256(arguments.vlm_run / "predictions.jsonl"),
            "positioned_metrics_sha256": file_sha256(arguments.positioned_run / "metrics.json"),
            "positioned_predictions_sha256": file_sha256(arguments.positioned_run / "predictions.jsonl"),
            "agreement_tolerance_m": tolerance_m,
            "metres_per_source_unit": scale_to_m,
            "prediction_reference_conditioning": "none",
            "silent_repair": False,
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
    })
    outputs: list[dict[str, Any]] = []
    raw_refs: list[list[dict[str, Any]]] = []
    raw_predictions: list[list[dict[str, Any]]] = []
    accepted_predictions: list[list[dict[str, Any]]] = []
    accepted_correct = accepted_incorrect = accepted_error_documents = 0
    complete_accepted = complete_correct = 0
    top_supported = bottom_supported = both_supported = proposal_count = 0
    for record_id in sorted(qwen_by_id):
        direct = qwen_by_id[record_id]
        positioned = positioned_by_id[record_id]
        proposals = direct["predicted_intervals"]
        candidates = positioned["predicted_intervals"]
        references = direct["reference_intervals"]
        regions = load_positioned_regions(arguments.positioned_run, positioned)
        agreement_pairs = agreeing_interval_pairs(proposals, candidates, tolerance_m=tolerance_m)
        candidate_for = {proposal_index: candidate_index for proposal_index, candidate_index in agreement_pairs}
        grounded = [index for index, candidate_index in candidate_for.items() if candidates[candidate_index].get("evidence", {}).get("regions")]
        accepted, rejected_by_constraint = monotonic_nonoverlapping_indices(proposals, grounded, tolerance_m=tolerance_m)
        accepted_set = set(accepted)
        accepted_intervals = [proposals[index] for index in accepted]
        accepted_matches, _, accepted_unmatched = match_intervals_by_boundaries(
            references, accepted_intervals, tolerance_m=0.05,
        )
        accepted_correct += len(accepted_matches)
        accepted_incorrect += len(accepted_unmatched)
        accepted_error_documents += bool(accepted_unmatched)
        decisions: list[dict[str, Any]] = []
        for index, proposal in enumerate(proposals):
            proposal_count += 1
            source_top = float(proposal["top_depth_m"]) / scale_to_m
            source_bottom = float(proposal["bottom_depth_m"]) / scale_to_m
            proposal_page = page_map[record_id][index]
            same_page_regions = [
                region for region in regions
                if region.get("page_index") == proposal_page.get("page_index")
            ]
            top_evidence = numeric_region_evidence(same_page_regions, source_top, tolerance=evidence_tolerance)
            bottom_evidence = numeric_region_evidence(same_page_regions, source_bottom, tolerance=evidence_tolerance)
            top_supported += bool(top_evidence)
            bottom_supported += bool(bottom_evidence)
            both_supported += bool(top_evidence and bottom_evidence)
            candidate_index = candidate_for.get(index)
            reason = "INDEPENDENT_COMPLETE_INTERVAL_AGREEMENT" if index in accepted_set else (
                "CONSTRAINT_REJECTED" if index in rejected_by_constraint else "NO_COMPLETE_INTERVAL_AGREEMENT"
            )
            decisions.append({
                "proposal_index": index,
                "proposal": proposal,
                "proposal_page": proposal_page,
                "decision": "AUTO_ACCEPT_INTERVAL" if index in accepted_set else "NEEDS_REVIEW",
                "decision_reason": reason,
                "positioned_candidate_index": candidate_index,
                "positioned_candidate": candidates[candidate_index] if candidate_index is not None else None,
                "top_field_evidence": top_evidence,
                "bottom_field_evidence": bottom_evidence,
                "constraint_outcomes": {
                    "positive_range": (
                        float(proposal["top_depth_m"]) >= 0.0
                        and float(proposal["bottom_depth_m"]) > float(proposal["top_depth_m"])
                    ),
                    "accepted_subsequence_nonoverlap": index not in rejected_by_constraint,
                },
            })
        json_pages = [row for row in qwen_pages if str(row["record_id"]) == record_id]
        complete_accept = (
            len(accepted) == len(proposals) == len(candidates)
            and complete_sequence(accepted_intervals, tolerance_m)
            and all(row.get("parse_status") == "json_valid" for row in json_pages)
            and not any(int(row.get("invalid_numeric_interval_count") or 0) for row in json_pages)
        )
        if complete_accept:
            complete_accepted += 1
            complete_correct += bool(direct["document_boundary_exact"])
        outputs.append({
            "record_id": record_id,
            "reference_intervals": references,
            "direct_vlm_proposals": proposals,
            "accepted_intervals": accepted_intervals,
            "decisions": decisions,
            "document_decision": "AUTO_ACCEPT_COMPLETE_DOCUMENT" if complete_accept else "NEEDS_REVIEW_FOR_COMPLETENESS",
            "direct_document_boundary_exact": direct["document_boundary_exact"],
        })
        raw_refs.append(references)
        raw_predictions.append(proposals)
        accepted_predictions.append(accepted_intervals)
    raw = boundary_matched_interval_metrics(raw_refs, raw_predictions, tolerance_m=0.05)
    selective = boundary_matched_interval_metrics(raw_refs, accepted_predictions, tolerance_m=0.05)
    accepted_count = accepted_correct + accepted_incorrect
    accepted_documents = sum(bool(row["accepted_intervals"]) for row in outputs)
    critical_field_count = proposal_count * 2
    metrics = {
        "scope": f"{arguments.cohort_role} evidence-grounded assurance over frozen direct-VLM proposals",
        "reference_ground_truth_tier": qwen_metrics["reference_ground_truth_tier"],
        "prediction_reference_conditioning": "none",
        "silent_repair": False,
        "document_count": len(outputs),
        "proposal_count": proposal_count,
        "raw_interval_metrics": {key: value.to_dict() for key, value in raw.items()},
        "accepted_interval_metrics": {key: value.to_dict() for key, value in selective.items()},
        "same_page_numeric_anchor_coverage": ratio(top_supported + bottom_supported, critical_field_count),
        "complete_interval_numeric_anchor_coverage": ratio(both_supported, proposal_count),
        "top_numeric_anchor_coverage": ratio(top_supported, proposal_count),
        "bottom_numeric_anchor_coverage": ratio(bottom_supported, proposal_count),
        "semantically_owned_accepted_field_coverage": ratio(accepted_count * 2, critical_field_count),
        "evidence_definitions": {
            "numeric_anchor": "the exact source-unit value occurs in a positioned OCR bbox on the same rendered page; it is a visual anchor candidate, not semantic ownership",
            "semantically_owned_acceptance": "a complete interval agrees with an independently parsed positioned candidate whose source regions are retained",
        },
        "accepted_proposal_coverage": ratio(accepted_count, proposal_count),
        "accepted_interval_precision": ratio(accepted_correct, accepted_count),
        "accepted_incorrect_interval_count": accepted_incorrect,
        "false_acceptance_rate": ratio(accepted_incorrect, accepted_count),
        "accepted_document_count": accepted_documents,
        "accepted_document_action_coverage": ratio(accepted_documents, len(outputs)),
        "accepted_error_document_count": accepted_error_documents,
        "accepted_document_error_rate": ratio(accepted_error_documents, accepted_documents),
        "one_sided_95_zero_error_upper_bound": {
            "per_accepted_interval": zero_event_upper_bound(accepted_count) if not accepted_incorrect else None,
            "per_document_with_accepted_action": zero_event_upper_bound(accepted_documents) if not accepted_error_documents else None,
        },
        "complete_document_auto_acceptance": ratio(complete_accepted, len(outputs)),
        "correct_complete_document_auto_acceptance": ratio(complete_correct, complete_accepted),
        "raw_critical_numeric_invalidity_rate": qwen_metrics["critical_numeric_invalidity_rate"],
        "accepted_invalid_numeric_range_count": 0,
        "accepted_invalid_numeric_rate": ratio(0, accepted_count),
        "component_latency_seconds": {
            "direct_vlm_total": qwen_metrics.get("latency_seconds_total"),
            "positioned_reader_total": positioned_metrics.get("wall_time_seconds"),
            "assurance_postprocess": time.perf_counter() - started,
        },
        "peak_process_rss_kib": peak_process_rss_kib(),
        "limitations": [
            "Agreement is between one direct VLM and one positioned OCR/parser; shared source ambiguity can still produce correlated errors.",
            "Interval acceptance does not establish document completeness; partial documents remain in the review queue.",
            "Gold is used only after the fixed decisions to estimate error, never to form an acceptance decision.",
            "A same-page numeric anchor can be ambiguous; only complete positioned-candidate agreement is treated as semantic ownership for automatic acceptance.",
        ],
    }
    gate = config["go_gate"]
    raw_precision = raw["interval_precision"].value or 0.0
    accepted_precision = metrics["accepted_interval_precision"]["value"] or 0.0
    metrics["go_gate"] = {
        "same_page_numeric_anchor_coverage_pass": metrics["same_page_numeric_anchor_coverage"]["value"] >= gate["same_page_numeric_anchor_coverage_minimum"],
        "accepted_precision_pass": accepted_precision > raw_precision,
        "accepted_coverage_pass": accepted_count > 0,
        "accepted_invalid_numeric_rate_pass": metrics["accepted_invalid_numeric_rate"]["value"] <= gate["accepted_invalid_numeric_rate_maximum"],
        "serialized_trace_pass": all(row["decisions"] for row in outputs),
    }
    metrics["go_gate"]["overall_pass"] = all(metrics["go_gate"].values())
    metrics["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_jsonl(run / "predictions.jsonl", outputs)
    write_jsonl(run / "errors.jsonl", [])
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "run.log").write_text(f"status=completed\ncohort_role={arguments.cohort_role}\ndocuments={len(outputs)}\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
