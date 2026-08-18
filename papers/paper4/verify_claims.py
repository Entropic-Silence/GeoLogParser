#!/usr/bin/env python3
"""Verify the headline numeric claims used by the integrated manuscript."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    modern = load("experiments/paper1/modern_vlm_result_summary_v001.json")
    assurance = load("experiments/paper2/analysis/vlm_proposal_assurance_v001.json")
    assurance_v003_metrics = load(
        "results/2026-08-17/P2_VLM_PROPOSAL_ASSURANCE_CALIFORNIA_V003_HELDOUT_002/metrics.json"
    )
    risk = load("experiments/paper2/analysis/california_document_risk_v001.json")
    spatial = load("experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json")
    completed_qwen = [
        row for row in modern["runs"]
        if row.get("model") == "Qwen3.8-27B-FP8" and "metrics" in row
    ]
    california_qwen = [row for row in completed_qwen if row["cohort"].startswith("California")]
    swissgeol_qwen = next(row for row in completed_qwen if row["cohort"] == "Swissgeol held-out")
    loo_reference = next(
        row["variants"]["reference"]["absolute_error_m"]["mean"]
        for row in spatial["leave_one_borehole_out"]
        if row["domain"] == "all_reference_targets" and row["neighbours"] == "all" and row["power"] == 2.0
    )
    checks = {
        "qwen_california_f1_range": [round(row["metrics"]["f1"], 3) for row in california_qwen] == [0.932, 0.896, 0.918, 0.917, 0.903],
        "qwen_boundary_exact_range": [row["metrics"]["boundary_exact"] for row in california_qwen] == [0.74, 0.70, 0.72, 0.74, 0.69],
        "qwen_swissgeol_f1": round(swissgeol_qwen["metrics"]["f1"], 3) == 0.577,
        "assurance_v003": (
            assurance["analyses"][2]["point_estimates"]["accepted_count"] == 447
            and assurance["analyses"][2]["point_estimates"]["accepted_correct_count"] == 444
            and round(assurance["analyses"][2]["point_estimates"]["accepted_precision"], 3) == 0.993
            and round(assurance["analyses"][2]["point_estimates"]["accepted_coverage"], 3) == 0.244
        ),
        "complete_document_auto_acceptance_v003": (
            assurance["analyses"][2]["complete_document_auto_acceptance"]["numerator"] == 4
            and assurance["analyses"][2]["complete_document_auto_acceptance"]["denominator"] == 100
            and round(assurance["analyses"][2]["complete_document_auto_acceptance"]["value"], 2) == 0.04
        ),
        "assurance_v003_anchor_units": (
            assurance_v003_metrics["same_page_numeric_anchor_coverage"] == {
                "denominator": 3666, "numerator": 3099, "value": 0.8453355155482815
            }
            and assurance_v003_metrics["complete_interval_numeric_anchor_coverage"] == {
                "denominator": 1833, "numerator": 1450, "value": 0.7910529187124932
            }
        ),
        "risk_actions": risk["combined_confirmatory"]["accepted_action_count"] == 82,
        "risk_documents": risk["combined_confirmatory"]["accepted_document_count"] == 19,
        "spatial_full_support": round(spatial["full_support_comparison"]["risk"]["aggregate"]["relative_absolute_volume_error"], 4) == 0.0821,
        "spatial_matched_subset": round(spatial["matched_subset_comparison"]["risk"]["aggregate"]["relative_absolute_volume_error"], 4) == 0.0754,
        "spatial_matched_raw": round(spatial["matched_subset_comparison"]["raw"]["aggregate"]["relative_absolute_volume_error"], 4) == 0.0326,
        "spatial_hull_ratio": round(spatial["spatial_support"][2]["convex_hull_area_ratio"], 3) == 0.636,
        "spatial_loo_reference": round(loo_reference, 2) == 47.06,
    }
    failed = [key for key, value in checks.items() if not value]
    report = {"checks": checks, "passed": len(failed) == 0, "failed": failed}
    output = ROOT / "papers/paper4/metric_audit.json"
    # Write bytes deliberately: Path.write_text() translates LF to CRLF on
    # Windows, which changes the SHA of committed generated JSON.
    output.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(report, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
