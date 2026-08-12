"""Pure paper-table renderers over immutable experiment outputs."""

from __future__ import annotations

import json
from pathlib import Path


def ratio(metric: dict) -> str:
    value = metric.get("value")
    return "TBD" if value is None else f"{metric['numerator']}/{metric['denominator']} ({value:.3f})"


def number(value, decimals: int = 3) -> str:
    return "TBD" if value is None else f"{value:.{decimals}f}"


def paper1_table(entries: list[dict], repository_root: Path) -> str:
    ocr_rows = []
    vlm_rows = []
    native_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        run = json.loads((repository_root / entry["result_path"] / "run.json").read_text())
        if "borehole_id_exact_match" in metrics:
            ocr_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"],
                ratio(metrics["borehole_id_exact_match"]),
                ratio(metrics["x_coordinate"]["x_coordinate_mae_coverage"]),
                number(metrics["x_coordinate"]["x_coordinate_mae"]["value"]),
                ratio(metrics["final_depth"]["final_depth_mae_m_coverage"]),
                str(metrics["total_intervals_emitted"]),
                number(metrics["latency_seconds_per_page"]),
                entry["paper_eligibility"],
            ]) + " |")
        elif "structured_parse_rate" in metrics:
            vlm_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["items"]),
                f'{metrics["schema_valid_responses"]}/{metrics["items"]} ({metrics["structured_parse_rate"]:.3f})',
                str(metrics["emitted_intervals"]), str(metrics["constraint_evaluations"]),
                str(metrics["constraint_violations"]),
                number(metrics["latency_mean_seconds_per_image"]),
                number(metrics["peak_gpu_memory_bytes"] / 1024**3),
                entry["paper_eligibility"],
            ]) + " |")
        elif "documents_with_borehole_id" in metrics:
            native_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["documents"]),
                f'{metrics["documents_with_borehole_id"]}/{metrics["documents"]}',
                f'{metrics["documents_with_final_depth"]}/{metrics["documents"]}',
                str(metrics["emitted_intervals"]), str(metrics["constraint_violations"]),
                number(metrics["latency_seconds_per_page"]), entry["paper_eligibility"],
            ]) + " |")
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "### OCR + regex audits",
        "",
        "| Experiment | Model | Borehole ID EM | X coverage | X paired MAE | Final-depth coverage | Emitted intervals | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *ocr_rows, "",
        "### VLM engineering audits",
        "",
        "| Experiment | Model | Images | Schema-valid | Emitted intervals | Constraint evals | Violations | s/image | Peak GiB | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *vlm_rows, "",
        "### Public native-PDF engineering audits",
        "",
        "| Experiment | Model | Documents | Borehole-ID coverage | Final-depth coverage | Emitted intervals | Violations | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *native_rows, "",
        "All rows are audit-only and not representative benchmark estimates. `TBD` paired MAE indicates zero paired predictions, not zero error. VLM audits have no human Ground Truth, so they report parse/diagnostic behavior rather than accuracy.",
    ]) + "\n"


def paper3_table(entries: list[dict], repository_root: Path) -> str:
    rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        for condition in metrics.get("conditions", []):
            if isinstance(condition.get("mae_m"), dict):
                mae = condition["mae_m"]
                rmse = condition["rmse_m"]
                maximum = condition["max_abs_error_m"]
                rows.append("| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    "multiple", str(condition["repetitions"]),
                    f'{number(mae["mean"], 6)} ± {number(mae["std"], 6)}',
                    f'{number(rmse["mean"], 6)} ± {number(rmse["std"], 6)}',
                    f'{number(maximum["mean"], 6)} ± {number(maximum["std"], 6)}',
                    entry["paper_eligibility"],
                ]) + " |")
            else:
                rows.append("| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    str(condition["seed"]), str(condition["count"]),
                    number(condition["mae_m"], 6), number(condition["rmse_m"], 6),
                    number(condition["max_abs_error_m"], 6), entry["paper_eligibility"],
                ]) + " |")
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *rows, "",
        "These rows are synthetic protocol results only; they are not evidence of real geological-model sensitivity. Multi-seed rows show mean ± sample standard deviation across seeds.",
    ]) + "\n"
