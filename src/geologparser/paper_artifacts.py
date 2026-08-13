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
    ocr_coverage_rows = []
    native_coverage_rows = []
    llm_rows = []
    layout_rows = []
    vlm_rows = []
    fusion_rows = []
    native_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        run = json.loads((repository_root / entry["result_path"] / "run.json").read_text())
        if "positioned_text_layout" in metrics.get("coverage_channels", []):
            native_coverage_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"],
                f'{metrics["completed_items"]}/{metrics["selected_items"]}',
                str(metrics["text_regions"]),
                f'{metrics["regex_items_with_borehole_id"]}/{metrics["completed_items"]}',
                f'{metrics["regex_items_with_any_interval"]}/{metrics["completed_items"]}',
                str(metrics["regex_emitted_intervals"]),
                f'{metrics["layout_items_with_any_interval"]}/{metrics["completed_items"]}',
                str(metrics["layout_emitted_intervals"]),
                str(metrics["layout_constraint_evaluations"]),
                str(metrics["layout_constraint_violations"]),
                number(metrics["latency_mean_seconds_per_item"]),
                entry["paper_eligibility"],
            ]) + " |")
        elif metrics.get("record_output_policy") == "hash_and_presence_only":
            ocr_coverage_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"],
                f'{metrics["completed_items"]}/{metrics["selected_items"]}',
                f'{metrics["items_with_borehole_id"]}/{metrics["completed_items"]}',
                f'{metrics["items_with_final_depth"]}/{metrics["completed_items"]}',
                f'{metrics["items_with_any_interval"]}/{metrics["completed_items"]}',
                str(metrics["emitted_intervals"]), str(metrics["ocr_regions"]),
                str(metrics["constraint_evaluations"]),
                str(metrics["constraint_violations"]),
                number(metrics["latency_mean_seconds_per_item"]),
                entry["paper_eligibility"],
            ]) + " |")
        elif "input_tokens_total" in metrics:
            llm_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["items"]),
                f'{metrics["schema_valid_responses"]}/{metrics["items"]} ({metrics["structured_parse_rate"]:.3f})',
                str(metrics["emitted_intervals"]), str(metrics["constraint_evaluations"]),
                str(metrics["constraint_violations"]), str(metrics["input_tokens_total"]),
                number(metrics["latency_mean_seconds_per_page"]),
                number(metrics["peak_gpu_memory_bytes"] / 1024**3), entry["paper_eligibility"],
            ]) + " |")
        elif "items_with_any_interval" in metrics:
            layout_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["items"]),
                f'{metrics["items_with_any_interval"]}/{metrics["items"]}',
                str(metrics["emitted_intervals"]), str(metrics["constraint_evaluations"]),
                str(metrics["constraint_violations"]),
                number(metrics["latency_mean_seconds_per_page"]), entry["paper_eligibility"],
            ]) + " |")
        elif "borehole_id_exact_match" in metrics:
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
        elif "items_with_schema_valid_vlm_record" in metrics:
            decisions = metrics["fusion_decision_counts"]
            fusion_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["items"]),
                f'{metrics["items_with_schema_valid_vlm_record"]}/{metrics["items"]}',
                str(decisions.get("agreement_keep_grounded_provenance", 0)),
                str(decisions.get("disagreement_keep_grounded_needs_review", 0)),
                str(decisions.get("visual_only_needs_review", 0)),
                str(decisions.get("vlm_unavailable_keep_grounded", 0)),
                str(metrics["emitted_intervals"]), entry["paper_eligibility"],
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
        "### Privacy-minimized OCR coverage audits (no Ground Truth)",
        "",
        "| Experiment | Model | Completed pages | Borehole-ID presence | Final-depth presence | Pages with intervals | Emitted intervals | OCR regions | Constraint evals | Violations | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *ocr_coverage_rows, "",
        "Presence and emitted-count columns are extraction coverage diagnostics, not accuracy estimates. Records and OCR text are not serialized; source pages remain unreviewed and have no human Ground Truth.",
        "",
        "### Privacy-minimized native-PDF coverage audits (no Ground Truth)",
        "",
        "| Experiment | Model | Completed pages | Text regions | Regex borehole-ID presence | Regex pages with intervals | Regex intervals | Layout pages with intervals | Layout intervals | Layout constraint evals | Violations | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *native_coverage_rows, "",
        "Direct-text and positioned-layout columns are extraction-path coverage diagnostics, not accuracy estimates. Persisted rows contain hashes and counts only; source text, extracted values, and source bboxes are omitted.",
        "",
        "### B2 text-only LLM engineering audits",
        "",
        "| Experiment | Model | Pages | Schema-valid | Emitted intervals | Constraint evals | Violations | Input tokens | s/page | Peak GiB | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *llm_rows, "",
        "### B3 positioned-text layout engineering audits",
        "",
        "| Experiment | Model | Pages | Pages with intervals | Emitted intervals | Constraint evals | Violations | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *layout_rows, "",
        "### VLM engineering audits",
        "",
        "| Experiment | Model | Images | Schema-valid | Emitted intervals | Constraint evals | Violations | s/image | Peak GiB | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *vlm_rows, "",
        "### B6 conservative fusion engineering audits",
        "",
        "| Experiment | Model | Items | VLM available | Agreements | Disagreements | Visual-only review | VLM unavailable | Emitted intervals | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *fusion_rows, "",
        "### Public native-PDF engineering audits",
        "",
        "| Experiment | Model | Documents | Borehole-ID coverage | Final-depth coverage | Emitted intervals | Violations | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *native_rows, "",
        "All rows are audit-only and not representative benchmark estimates. `TBD` paired MAE indicates zero paired predictions, not zero error. VLM audits have no human Ground Truth, so they report parse/diagnostic behavior rather than accuracy.",
    ]) + "\n"


def paper3_table(entries: list[dict], repository_root: Path) -> str:
    synthetic_rows = []
    source_protocol_rows = []
    interoperability_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        source_protocol = metrics.get("data_status") == "licensed_source_structured_data_pending_human_spatial_review"
        for condition in metrics.get("conditions", []):
            if isinstance(condition.get("mae_m"), dict):
                mae = condition["mae_m"]
                rmse = condition["rmse_m"]
                maximum = condition["max_abs_error_m"]
                row = "| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    "multiple", str(condition["repetitions"]),
                    f'{number(mae["mean"], 6)} ± {number(mae["std"], 6)}',
                    f'{number(rmse["mean"], 6)} ± {number(rmse["std"], 6)}',
                    f'{number(maximum["mean"], 6)} ± {number(maximum["std"], 6)}',
                    entry["paper_eligibility"],
                ]) + " |"
            else:
                row = "| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    str(condition["seed"]), str(condition["count"]),
                    number(condition["mae_m"], 6), number(condition["rmse_m"], 6),
                    number(condition["max_abs_error_m"], 6), entry["paper_eligibility"],
                ]) + " |"
            (source_protocol_rows if source_protocol else synthetic_rows).append(row)
        if "surface_vtp_sha256" in metrics:
            interoperability_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics["point_count"]),
                str(metrics["triangle_cell_count"]),
                ", ".join(number(value, 3) for value in metrics["bounds"]),
                metrics["surface_vtp_sha256"], metrics["surface_png_sha256"],
                entry["paper_eligibility"],
            ]) + " |")
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "### Synthetic error-propagation protocol",
        "",
        "| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *synthetic_rows, "",
        "These rows are synthetic protocol results only; they are not evidence of real geological-model sensitivity. Multi-seed rows show mean ± sample standard deviation across seeds.",
        "",
        "### Licensed structured-source field proxy protocol",
        "",
        "| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Proxy-surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *source_protocol_rows, "",
        "These rows use source-reported tabular values with origin-suppressed local coordinates. They are protocol-development evidence only, not AI extraction, Ground Truth, constraint-QC, true geological-surface, absolute-location, or formal downstream evidence. Multi-seed rows show mean ± sample standard deviation across seeds.",
        "",
        "### Synthetic 3D interoperability protocol",
        "",
        "| Experiment | Points | Triangle cells | Bounds (x0, x1, y0, y1, z0, z1) | VTP SHA256 | PNG SHA256 | Eligibility |",
        "|---|---:|---:|---|---|---|---|",
        *interoperability_rows, "",
        "Interoperability rows establish reproducible artifact generation only; they do not establish geological validity or real-site performance.",
    ]) + "\n"


def paper2_table(entries: list[dict], repository_root: Path) -> str:
    rows = []
    audit_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        if "vlm_schema_valid_count" in metrics:
            audit_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics["case_count"]),
                f'{metrics["vlm_schema_valid_count"]}/{metrics["case_count"]}',
                str(metrics["vlm_uncertain_count"]),
                str(metrics["cross_reader_numeric_agreement_case_count"]),
                str(metrics["accept_proposal_count"]), str(metrics["needs_review_count"]),
                number(metrics["vlm_latency_mean_seconds_per_roi"]),
                number(metrics["peak_gpu_memory_bytes"] / 1024**3),
                entry["paper_eligibility"],
            ]) + " |")
        if metrics.get("protocol") != "paper2_one_module_ablation_matrix_v001":
            continue
        for variant_name, variant in metrics["variants"].items():
            values = variant["metrics"]
            correction = values["correction"]
            review = values["review"]
            confidence = values["confidence"]
            rows.append("| " + " | ".join([
                entry["experiment_id"], variant_name,
                ", ".join(variant["disabled_modules"]) or "none",
                str(values["calibration_case_count"]), str(values["test_case_count"]),
                ratio(correction["correction_success_rate"]),
                ratio(correction["false_correction_rate"]),
                ratio(review["manual_review_recall"]),
                ratio(review["review_rate"]),
                ratio(review["auto_accept_error_rate"]),
                number(confidence["raw_expected_calibration_error"]["value"]),
                number(confidence["calibrated_expected_calibration_error"]["value"]),
                entry["paper_eligibility"],
            ]) + " |")
    formal_section = [
        "### Human-GT-gated method and ablation results", "",
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "| Experiment | Variant | Disabled | Calibration n | Test n | Correction success | FCR | Review recall | Review rate | Auto-accept error | Raw ECE | Calibrated ECE | Eligibility |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *rows,
    ]
    if not rows:
        formal_section.append("| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | no formal run |")
    formal_section.extend(["",
        "Rows are generated only from human-GT-gated, identical-case, one-module-at-a-time ablation matrices.",
    ])
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "### Public ROI engineering audit (no Ground Truth)", "",
        "| Experiment | Cases | VLM JSON-valid | VLM uncertain | OCR/VLM numeric-agreement cases | Accept proposals | Needs review | VLM s/ROI | Peak GiB | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *audit_rows, "",
        "These rows report parser, candidate-path, latency, and resource behavior only. Source annotations are `auto`; accuracy, correction success, and FCR are undefined.",
        "", *formal_section,
    ]) + "\n"
