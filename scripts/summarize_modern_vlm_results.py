#!/usr/bin/env python3
"""Generate a traceable modern-VLM comparison table from formal run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def fmt(value: object, digits: int = 3) -> str:
    return "-" if value is None else f"{float(value):.{digits}f}"


def read_completed(entry: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / str(entry["result_path"])
    metrics_path = path / "metrics.json"
    run_log_path = path / "run.log"
    if not metrics_path.is_file() or not run_log_path.is_file() or "status=completed" not in run_log_path.read_text(encoding="utf-8"):
        raise ValueError(f"{entry['experiment_id']} is marked COMPLETED without a complete formal run")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if metrics.get("scope") is None:
        raise ValueError(f"{entry['experiment_id']} lacks formal metrics")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/experiments/paper1_modern_vlm_result_plan_v001.json")
    parser.add_argument("--output", type=Path, default=ROOT / "papers/paper1/generated/modern_vlm_results.md")
    parser.add_argument("--json-output", type=Path, default=ROOT / "experiments/paper1/modern_vlm_result_summary_v001.json")
    parser.add_argument("--statistics", type=Path, default=ROOT / "experiments/paper1/analysis/modern_vlm_statistics_v001.json")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    statistics = json.loads(args.statistics.read_text(encoding="utf-8")) if args.statistics.is_file() else {"analyses": {}}
    published: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    for entry in plan["runs"]:
        row = dict(entry)
        if entry["status"] == "COMPLETED":
            metrics = read_completed(entry)
            interval = metrics["interval_metrics"]
            row["metrics"] = {
                "documents": metrics["document_count"],
                "pages": metrics["page_count"],
                "precision": interval["interval_precision"]["value"],
                "recall": interval["interval_recall"]["value"],
                "f1": interval["interval_f1"]["value"],
                "boundary_exact": metrics["document_boundary_exact"]["value"],
                "zero_output": metrics["zero_output_document_rate"],
                "json_valid": metrics.get("json_valid_page_rate"),
                "numeric_invalidity": metrics.get("critical_numeric_invalidity_rate"),
                "seconds_per_page": metrics.get("latency_seconds_per_page"),
            }
            row["statistics"] = statistics.get("analyses", {}).get(entry["experiment_id"])
            published.append(row)
        summary.append(row)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps({"protocol": plan["protocol"], "runs": summary}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Modern VLM Results",
        "",
        "This table is generated only from runs whose artifact directory records `status=completed`. Metrics with different evidence tiers are never pooled.",
        "",
        "| Group | Model | Interface | Cohort | Evidence | Docs | Pages | P | R | F1 (document 95% CI) | Boundary-exact | Zero output | JSON-valid | Numeric invalidity | s/page |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in published:
        value = row["metrics"]
        ci = (row.get("statistics") or {}).get("document_cluster_metrics", {}).get("bootstrap_percentile_95_ci", {}).get("f1")
        f1 = f"{fmt(value['f1'])} [{fmt(ci[0])}, {fmt(ci[1])}]" if ci else fmt(value["f1"])
        lines.append(
            f"| {row['group']} | {row['model']} | {row['interface']} | {row['cohort']} | {row['evidence_tier']} | "
            f"{value['documents']} | {value['pages']} | {fmt(value['precision'])} | {fmt(value['recall'])} | {f1} | "
            f"{fmt(value['boundary_exact'])} | {fmt(value['zero_output'])} | {fmt(value['json_valid'])} | "
            f"{fmt(value['numeric_invalidity'])} | {fmt(value['seconds_per_page'], 2)} |"
        )
    paired_rows = [
        row for row in published
        if (row.get("statistics") or {}).get("paired_against_frozen_rapidocr")
    ]
    if paired_rows:
        lines.extend([
            "",
            "## Paired California Comparison",
            "",
            "The following deltas resample whole reports while retaining the paired Qwen and frozen RapidOCR predictions. They apply only to the published-manual-transcription California cohorts; they are not pooled with the Swissgeol source-agreement panel.",
            "",
            "| Cohort | Qwen F1 | RapidOCR F1 | Delta F1 (Qwen - RapidOCR), document 95% CI | Bootstrap Pr(delta > 0) |",
            "| --- | ---: | ---: | ---: | ---: |",
        ])
        for row in paired_rows:
            paired = row["statistics"]["paired_against_frozen_rapidocr"]
            delta = paired["delta_left_minus_right"]["f1"]
            ci = delta["bootstrap_percentile_95_ci"]
            lines.append(
                f"| {row['cohort']} | {fmt(row['metrics']['f1'])} | {fmt(paired['right']['f1'])} | "
                f"{fmt(delta['observed'])} [{fmt(ci[0])}, {fmt(ci[1])}] | "
                f"{fmt(delta['bootstrap_probability_delta_gt_zero'])} |"
            )
    if not published:
        lines.append("| - | No completed modern baseline | - | - | - | - | - | - | - | - | - | - | - | - | - |")
    pending_rows = [
        row for row in summary
        if row["status"] != "COMPLETED" and not str(row["status"]).startswith("TRANSPORT_INTERRUPTED")
    ]
    interrupted_rows = [
        row for row in summary
        if str(row["status"]).startswith("TRANSPORT_INTERRUPTED")
    ]
    lines.extend([
        "",
        "## Registered But Not Yet Comparable",
        "",
        "| Group | Model | Cohort | Status |",
        "| --- | --- | --- | --- |",
    ])
    for row in pending_rows:
        lines.append(f"| {row['group']} | {row['model']} | {row['cohort']} | {row['status']} |")
    if interrupted_rows:
        lines.extend([
            "",
            "## Retained Operational Records",
            "",
            "The interrupted v004 attempts are retained for transport auditing only. They have no score and were superseded by the completed frozen v004 run above; no page was selectively retried.",
            "",
            "| Model | Cohort | Status |",
            "| --- | --- | --- |",
        ])
        for row in interrupted_rows:
            lines.append(f"| {row['model']} | {row['cohort']} | {row['status']} |")
    lines.extend([
        "",
        "## Interpretation Boundary",
        "",
        "Direct extraction quality is distinct from assurance capability. The comparison may attribute an assurance property to GeoLogParser only when the corresponding run records field-level source geometry, deterministic numeric checks, constraint outcomes, an explicit acceptance or abstention decision, and database provenance. A registered or unavailable closed model contributes no score and no comparative conclusion.",
        "",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
