#!/usr/bin/env python3
"""Generate Paper II assurance statistics from immutable result artifacts."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Callable

from geologparser.evaluation import match_intervals_by_boundaries
from geologparser.result_index import file_sha256


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def document_counts(row: dict[str, Any]) -> dict[str, int]:
    proposals = row["direct_vlm_proposals"]
    accepted = row["accepted_intervals"]
    references = row["reference_intervals"]
    raw_matches = match_intervals_by_boundaries(references, proposals, tolerance_m=0.05)[0]
    accepted_matches = match_intervals_by_boundaries(references, accepted, tolerance_m=0.05)[0]
    return {
        "proposal": len(proposals),
        "raw_correct": len(raw_matches),
        "accepted": len(accepted),
        "accepted_correct": len(accepted_matches),
        "accepted_document": int(bool(accepted)),
        "error_document": int(len(accepted_matches) < len(accepted)),
    }


def aggregate(rows: list[dict[str, int]]) -> dict[str, float | int | None]:
    proposal = sum(row["proposal"] for row in rows)
    raw_correct = sum(row["raw_correct"] for row in rows)
    accepted = sum(row["accepted"] for row in rows)
    accepted_correct = sum(row["accepted_correct"] for row in rows)
    accepted_documents = sum(row["accepted_document"] for row in rows)
    error_documents = sum(row["error_document"] for row in rows)
    return {
        "proposal_count": proposal,
        "raw_precision": raw_correct / proposal if proposal else None,
        "accepted_count": accepted,
        "accepted_correct_count": accepted_correct,
        "accepted_precision": accepted_correct / accepted if accepted else None,
        "accepted_coverage": accepted / proposal if proposal else None,
        "false_acceptance_rate": (accepted - accepted_correct) / accepted if accepted else None,
        "accepted_document_count": accepted_documents,
        "accepted_document_error_rate": error_documents / accepted_documents if accepted_documents else None,
    }


def bootstrap(
    rows: list[dict[str, int]], repetitions: int, rng: random.Random,
) -> dict[str, list[float]]:
    fields: dict[str, Callable[[dict[str, float | int | None]], float | None]] = {
        "accepted_precision": lambda result: result["accepted_precision"],
        "accepted_coverage": lambda result: result["accepted_coverage"],
        "false_acceptance_rate": lambda result: result["false_acceptance_rate"],
        "accepted_document_error_rate": lambda result: result["accepted_document_error_rate"],
    }
    samples = {key: [] for key in fields}
    for _ in range(repetitions):
        result = aggregate([rows[rng.randrange(len(rows))] for _ in rows])
        for key, accessor in fields.items():
            value = accessor(result)
            if value is not None:
                samples[key].append(float(value))
    return {
        key: [percentile(values, 0.025), percentile(values, 0.975)]
        for key, values in samples.items() if values
    }


def fmt(value: float | None, digits: int = 3) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/experiments/paper2_vlm_proposal_assurance_result_plan_v001.json")
    parser.add_argument("--json-output", type=Path, default=ROOT / "experiments/paper2/analysis/vlm_proposal_assurance_v001.json")
    parser.add_argument("--markdown-output", type=Path, default=ROOT / "papers/paper2/generated/vlm_proposal_assurance_v001.md")
    arguments = parser.parse_args()
    plan = json.loads(arguments.plan.read_text(encoding="utf-8"))
    rng = random.Random(int(plan["bootstrap_seed"]))
    analyses: list[dict[str, Any]] = []
    for entry in plan["runs"]:
        result_path = ROOT / entry["result_path"]
        metrics_path = result_path / "metrics.json"
        predictions_path = result_path / "predictions.jsonl"
        run_log = (result_path / "run.log").read_text(encoding="utf-8")
        if "status=completed" not in run_log:
            raise ValueError(f"incomplete result: {entry['experiment_id']}")
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        rows = [document_counts(row) for row in load_jsonl(predictions_path)]
        point = aggregate(rows)
        expected_precision = metrics["accepted_interval_metrics"]["interval_precision"]["value"]
        if point["accepted_precision"] != expected_precision or metrics["accepted_interval_precision"]["value"] != expected_precision:
            raise ValueError(f"accepted-subset precision mismatch: {entry['experiment_id']}")
        expected_incorrect = metrics["accepted_interval_metrics"]["interval_precision"]["details"]["unmatched_prediction_count"]
        if int(point["accepted_count"]) - int(point["accepted_correct_count"]) != expected_incorrect:
            raise ValueError(f"accepted-subset error count mismatch: {entry['experiment_id']}")
        analyses.append({
            **entry,
            "metrics_sha256": file_sha256(metrics_path),
            "predictions_sha256": file_sha256(predictions_path),
            "point_estimates": point,
            "document_cluster_bootstrap_percentile_95_ci": bootstrap(
                rows, int(plan["bootstrap_repetitions"]), rng,
            ),
            "same_page_numeric_anchor_coverage": metrics["same_page_numeric_anchor_coverage"]["value"],
            "semantically_owned_field_coverage": metrics["semantically_owned_accepted_field_coverage"]["value"],
            "complete_document_auto_acceptance": metrics["complete_document_auto_acceptance"],
            "correct_complete_document_auto_acceptance": metrics["correct_complete_document_auto_acceptance"],
            "go_gate": metrics["go_gate"],
        })
    report = {
        "protocol": plan["protocol"],
        "bootstrap_unit": "document",
        "bootstrap_repetitions": plan["bootstrap_repetitions"],
        "bootstrap_seed": plan["bootstrap_seed"],
        "analyses": analyses,
        "interpretation": "Same-page numeric anchors are occurrence-level visual evidence, not semantic ownership. Only complete interval agreement with positioned candidate evidence is automatically accepted.",
    }
    arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# VLM Proposal Assurance",
        "",
        "Evidence tier: **Published manual transcription Gold**. The direct VLM and positioned reader are frozen independently; Gold is used only after decisions. Confidence intervals use document-cluster bootstrap.",
        "",
        "| Cohort | Role | Raw P | Numeric-anchor coverage | Owned/accepted coverage | Accepted actions | Selective P (95% CI) | False acceptance | Docs with actions | Error docs |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in analyses:
        point = row["point_estimates"]
        ci = row["document_cluster_bootstrap_percentile_95_ci"]["accepted_precision"]
        error_documents = round(
            float(point["accepted_document_error_rate"]) * int(point["accepted_document_count"])
        ) if point["accepted_document_error_rate"] is not None else 0
        lines.append(
            f"| {row['cohort']} | {row['role']} | {fmt(point['raw_precision'])} | "
            f"{fmt(row['same_page_numeric_anchor_coverage'])} | {fmt(row['semantically_owned_field_coverage'])} | "
            f"{point['accepted_count']} | {fmt(point['accepted_precision'])} [{fmt(ci[0])}, {fmt(ci[1])}] | "
            f"{fmt(point['false_acceptance_rate'])} | {point['accepted_document_count']} | {error_documents} |"
        )
    lines.extend([
        "",
        "Numeric-anchor coverage means that the exact source-unit value occurs in a positioned bbox on the same page; it does not establish column ownership. Owned/accepted coverage requires complete top-bottom agreement with the independently parsed positioned interval and retained source regions. Partial acceptance does not establish document completeness, so all non-complete documents remain in the review queue.",
        "",
    ])
    arguments.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.markdown_output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
