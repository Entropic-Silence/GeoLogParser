#!/usr/bin/env python3
"""Audit routed-parser coverage on a source outside the BGS development corpus.

The audit intentionally does not retune the BGS experts.  It measures whether
the existing page-family gate can recognize and route an independent source;
unsupported pages abstain instead of being forced through a mismatched expert.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geologparser.layout import classify_borehole_page
from scripts.run_bgs_layout_method_development import boundary_metrics, interval_metrics


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def boundaries(row: dict) -> list[float]:
    return sorted({
        float(value)
        for interval in row["intervals"]
        for value in (interval["top_depth_m"], interval["bottom_depth_m"])
    })


def prediction_boundaries(row: dict) -> list[float]:
    values = []
    for interval in row.get("predicted_intervals", []):
        values.extend((float(interval["top_depth_m"]), float(interval["bottom_depth_m"])))
    return sorted(set(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--baseline-predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = load_jsonl(args.manifest)
    baseline_rows = {row["record_id"]: row for row in load_jsonl(args.baseline_predictions)}
    gold = {row["record_id"]: boundaries(row) for row in manifest}
    baseline = {record_id: prediction_boundaries(baseline_rows[record_id]) for record_id in gold}
    routed: dict[str, list[float]] = {}
    family_counts: dict[str, int] = {}
    diagnostics = []
    for row in manifest:
        record_id = row["record_id"]
        families = []
        evidence = []
        for page in row["evaluation_pages"]:
            image_path = args.source_run / f"{record_id}_page-{page}.png"
            region_path = args.source_run / f"{record_id}_page-{page}_regions.jsonl"
            regions = load_jsonl(region_path)
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                family = "unsupported"
                page_evidence = ["image_decode_failure"]
            else:
                assessment = classify_borehole_page(regions, width=image.shape[1], height=image.shape[0])
                family = assessment.family
                page_evidence = list(assessment.evidence)
            families.append(family)
            evidence.extend(page_evidence)
            family_counts[family] = family_counts.get(family, 0) + 1
        if not families or "unsupported" in families:
            route = "abstain_unsupported_family"
            routed[record_id] = []
        else:
            route = "v024_baseline_expert"
            routed[record_id] = baseline[record_id]
        diagnostics.append({
            "record_id": record_id,
            "page_families": families,
            "route": route,
            "baseline_boundary_count": len(baseline[record_id]),
            "routed_boundary_count": len(routed[record_id]),
            "evidence": sorted(set(evidence)),
        })
    supported_pages = sum(count for family, count in family_counts.items() if family != "unsupported")
    total_pages = sum(family_counts.values())
    if supported_pages:
        interpretation = (
            "The multilingual family aliases restored selective page support, but the routed values are unchanged baseline-expert predictions on the recognized subset. "
            "This is evidence for family-gating coverage and abstention, not a new extraction-expert gain or an overall F1 improvement."
        )
    else:
        interpretation = (
            "No expert gain can be claimed on this source because the BGS family detector classified every page as unsupported; "
            "the routed result is a coverage/no-go audit, not a tuned source-specific method result."
        )
    report = {
        "experiment_id": args.experiment_id,
        "status": "completed_independent_source_coverage_audit",
        "source_scope": "Swissgeol Thurgau v003 development, independent of BGS v001/v002/v003",
        "manifest": str(args.manifest),
        "source_run": str(args.source_run),
        "baseline_predictions": str(args.baseline_predictions),
        "document_count": len(manifest),
        "page_count": sum(len(row["evaluation_pages"]) for row in manifest),
        "family_counts": family_counts,
        "route_counts": {route: sum(row["route"] == route for row in diagnostics) for route in sorted({row["route"] for row in diagnostics})},
        "baseline": {
            "boundary": boundary_metrics(baseline, gold, 0.05),
            "interval": interval_metrics(baseline, gold, 0.05),
        },
        "routed": {
            "boundary": boundary_metrics(routed, gold, 0.05),
            "interval": interval_metrics(routed, gold, 0.05),
        },
        "coverage": {
            "baseline_documents_with_predictions": sum(bool(values) for values in baseline.values()),
            "routed_documents_with_predictions": sum(bool(values) for values in routed.values()),
            "routed_page_family_support_rate": supported_pages / max(1, total_pages),
        },
        "diagnostics": diagnostics,
        "interpretation": interpretation,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"family_counts": family_counts, "baseline": report["baseline"], "routed": report["routed"]}, indent=2))


if __name__ == "__main__":
    main()
