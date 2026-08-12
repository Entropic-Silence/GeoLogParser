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
    rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        run = json.loads((repository_root / entry["result_path"] / "run.json").read_text())
        rows.append("| " + " | ".join([
            entry["experiment_id"], run["model"],
            ratio(metrics["borehole_id_exact_match"]),
            ratio(metrics["x_coordinate"]["x_coordinate_mae_coverage"]),
            number(metrics["x_coordinate"]["x_coordinate_mae"]["value"]),
            ratio(metrics["final_depth"]["final_depth_mae_m_coverage"]),
            str(metrics["total_intervals_emitted"]),
            number(metrics["latency_seconds_per_page"]),
            entry["paper_eligibility"],
        ]) + " |")
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "| Experiment | Model | Borehole ID EM | X coverage | X paired MAE | Final-depth coverage | Emitted intervals | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *rows, "",
        "All rows are fixed four-document BGS audits, not representative benchmark estimates. `TBD` paired MAE indicates zero paired predictions, not zero error.",
    ]) + "\n"


def paper3_table(entries: list[dict], repository_root: Path) -> str:
    rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        for condition in metrics.get("conditions", []):
            rows.append("| " + " | ".join([
                entry["experiment_id"], number(condition["magnitude_m"], 2),
                str(condition["seed"]), str(condition["count"]),
                number(condition["mae_m"], 6), number(condition["rmse_m"], 6),
                number(condition["max_abs_error_m"], 6), entry["paper_eligibility"],
            ]) + " |")
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "| Experiment | Perturbation (m) | Seed | Grid points | Surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *rows, "",
        "These rows are synthetic protocol smoke results only; they are not evidence of real geological-model sensitivity.",
    ]) + "\n"
