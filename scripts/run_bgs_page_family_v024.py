#!/usr/bin/env python3
"""Run the v024 page-family and structural-risk route.

This is deliberately a routing experiment, not a retuned v023 ranker.  The
existing candidate model is retained for supported pages; explicit range-table
pages use an independent, high-resolution parser; unsupported or candidate-
explosion pages abstain at document level.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import cv2

from geologparser.layout import (
    boundaries_from_ranges, classify_borehole_page, extract_explicit_depth_ranges,
)
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def references(row: dict) -> list[float]:
    return sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})


def report_predictions(report: dict) -> dict[str, list[float]]:
    return {
        row["record_id"]: [float(value) for value in row.get("predicted_boundaries_m", [])]
        for row in report.get("predictions", [])
    }


def report_candidate_counts(report: dict) -> dict[str, int]:
    output = {}
    for row in report.get("predictions", []):
        if "candidate_count" in row:
            output[row["record_id"]] = int(row["candidate_count"])
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--evaluation-role", choices=("development", "validation"), default="development")
    parser.add_argument("--candidate-explosion-per-page", type=int, default=1000)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    sources = load_jsonl(args.manifest)
    baseline = json.loads(args.baseline_report.read_text(encoding="utf-8"))
    candidate_report = json.loads(args.candidate_report.read_text(encoding="utf-8"))
    baseline_predictions = report_predictions(baseline)
    candidate_counts = report_candidate_counts(candidate_report)
    references_by_id = {row["record_id"]: references(row) for row in sources}

    predictions: dict[str, list[float]] = {}
    evidence: dict[str, list[dict]] = {}
    diagnostics: list[dict] = []
    for source in sources:
        record_id = source["record_id"]
        page_rows = []
        explicit_ranges = []
        page_families = []
        page_risks = []
        pages = list(source["evaluation_pages"])
        for page in pages:
            image_path = args.source_run / f"{record_id}_page-{page}.png"
            region_path = args.source_run / f"{record_id}_page-{page}_regions.jsonl"
            if not image_path.exists() or not region_path.exists():
                page_families.append("unsupported")
                page_risks.append("missing_page_evidence")
                continue
            rows = load_jsonl(region_path)
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                page_families.append("unsupported")
                page_risks.append("image_decode_failure")
                continue
            assessment = classify_borehole_page(rows, width=image.shape[1], height=image.shape[0])
            page_families.append(assessment.family)
            if assessment.family == "explicit_depth_range_table":
                ranges, range_diag = extract_explicit_depth_ranges(image_path, rows, page=page)
                page_rows.append({"page": page, "family": assessment.family, "assessment": assessment.evidence, "range_diagnostic": range_diag, "range_count": len(ranges)})
                if ranges:
                    explicit_ranges.extend(ranges)
                else:
                    page_risks.append("explicit_range_abstention")
            else:
                page_rows.append({"page": page, "family": assessment.family, "assessment": assessment.evidence})

        baseline_values = baseline_predictions.get(record_id, [])
        document_candidates = candidate_counts.get(record_id, 0)
        candidate_per_page = document_candidates / max(1, len(pages))
        risk_codes = list(page_risks)
        route = "baseline_v023"
        if explicit_ranges:
            predicted = boundaries_from_ranges(explicit_ranges)
            route = "explicit_range_parser"
            document_evidence = [
                {
                    "value_m": row.top_m,
                    "page": row.page,
                    "bbox": list(row.bbox),
                    "candidate_source": "explicit_depth_range_table",
                    "source_texts": list(row.source_texts),
                    "view_support": row.view_support,
                    "score": row.score,
                }
                for row in explicit_ranges
            ]
            document_evidence.extend(
                {
                    "value_m": row.bottom_m,
                    "page": row.page,
                    "bbox": list(row.bbox),
                    "candidate_source": "explicit_depth_range_table",
                    "source_texts": list(row.source_texts),
                    "view_support": row.view_support,
                    "score": row.score,
                }
                for row in explicit_ranges
            )
        elif not page_families or any(family == "unsupported" for family in page_families):
            predicted = []
            document_evidence = []
            route = "abstain_unsupported_page_family"
            risk_codes.append("unsupported_page_family")
        elif not baseline_values:
            predicted = []
            document_evidence = []
            route = "abstain_zero_structural_evidence"
            risk_codes.append("zero_structural_evidence")
        elif (
            candidate_per_page > args.candidate_explosion_per_page
            and (
                len(baseline_values) >= 40
                or len(baseline_values) / max(1, document_candidates) >= 0.03
            )
        ):
            predicted = []
            document_evidence = []
            route = "abstain_candidate_explosion"
            risk_codes.append("candidate_explosion")
        else:
            predicted = baseline_values
            document_evidence = []
            route = "baseline_v023"

        predictions[record_id] = predicted
        evidence[record_id] = document_evidence
        diagnostics.append({
            "record_id": record_id,
            "page_count": len(pages),
            "page_families": page_families,
            "page_rows": page_rows,
            "baseline_boundary_count": len(baseline_values),
            "candidate_count": document_candidates,
            "candidate_count_per_page": candidate_per_page,
            "route": route,
            "risk_codes": sorted(set(risk_codes)),
            "predicted_boundaries_m": predicted,
            "provenance_count": len(document_evidence),
        })

    references_for_scoring = references_by_id
    metrics = {
        f"{tolerance:.2f}": {
            "boundary": boundary_metrics(predictions, references_for_scoring, tolerance),
            "interval": interval_metrics(predictions, references_for_scoring, tolerance),
        }
        for tolerance in (0.01, 0.05, 0.10)
    }
    accepted = sum(len(values) for values in predictions.values())
    reference_count = sum(len(values) for values in references_for_scoring.values())
    report = {
        "experiment_id": args.experiment_id,
        "status": f"completed_{args.evaluation_role}_evaluation",
        "evaluation_role": args.evaluation_role,
        "method_version": "bgs_page_family_structural_risk_v024",
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "baseline_report": str(args.baseline_report),
        "baseline_report_sha256": sha256(args.baseline_report),
        "candidate_report": str(args.candidate_report),
        "candidate_report_sha256": sha256(args.candidate_report),
        "source_run": str(args.source_run),
        "source_regions_sha256": sha256(args.source_run / "predictions.jsonl"),
        "document_count": len(sources),
        "page_count": sum(len(row["evaluation_pages"]) for row in sources),
        "reference_interval_count": sum(len(row["intervals"]) for row in sources),
        "reference_boundary_count": reference_count,
        "metrics_by_tolerance_m": metrics,
        "selective_operating_point": {
            "accepted_boundary_count": accepted,
            "coverage_against_reference": accepted / reference_count if reference_count else 0.0,
            "boundary": metrics["0.05"]["boundary"],
            "interval": metrics["0.05"]["interval"],
        },
        "risk_policy": {
            "candidate_explosion_per_page": args.candidate_explosion_per_page,
            "candidate_explosion_output_count_minimum": 40,
            "candidate_explosion_output_fraction_minimum": 0.03,
            "unsupported_page_family": "document_abstention",
            "zero_structural_evidence": "document_abstention",
        },
        "predictions": diagnostics,
        "reference_blinding": "baseline and candidate routing are fixed before validation references are used for scoring",
        "limitations": [
            "Explicit range extraction is currently conservative and may abstain on degraded later rows.",
            "Graphical contact and scaled composite pages still use v023 geometry only when structural-risk gates pass.",
            "This artifact is validation evidence for consumed BGS v002r2; it is not external confirmation.",
        ],
        "wall_time_seconds": time.perf_counter() - started,
        "latency_seconds_per_page": (time.perf_counter() - started) / max(1, sum(len(row["evaluation_pages"]) for row in sources)),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"metrics_at_0.05m": metrics["0.05"], "selective": report["selective_operating_point"], "routes": {row["route"]: sum(1 for item in diagnostics if item["route"] == row["route"]) for row in diagnostics}}, indent=2))


if __name__ == "__main__":
    main()
