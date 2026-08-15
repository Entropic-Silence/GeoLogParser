"""Pure paper-table renderers over immutable experiment outputs."""

from __future__ import annotations

import json
from pathlib import Path


def ratio(metric: dict) -> str:
    """Render a ratio metric without inventing values for unavailable fields.

    Some cross-source audits intentionally report only interval-level metrics and
    therefore do not define document-level exactness.  Paper tables should keep
    that distinction explicit instead of failing generation or silently treating
    a missing metric as zero.
    """
    if not metric or metric.get("value") is None:
        return "TBD"
    if "numerator" not in metric or "denominator" not in metric:
        return "TBD"
    return f"{metric['numerator']}/{metric['denominator']} ({metric['value']:.3f})"


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
    synthetic_rows = []
    silver_rows = []
    authoritative_interval_rows = []
    cross_source_interval_rows = []
    conditional_interval_rows = []
    development_interval_rows = []
    source_disjoint_transfer_rows = []
    published_manual_gold_rows = []
    robustness_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        run = json.loads((repository_root / entry["result_path"] / "run.json").read_text())
        if metrics.get("scope") == "human-GT benchmark evaluation":
            interval = metrics["interval_metrics"]
            published_manual_gold_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["document_count"]),
                str(metrics["county_count"]), str(metrics["page_count"]),
                str(metrics["reference_interval_count"]), str(metrics["predicted_interval_count"]),
                str(metrics["documents_with_predictions"]),
                number(interval["interval_precision"]["value"]),
                number(interval["interval_recall"]["value"]),
                number(interval["interval_f1"]["value"]),
                ratio(metrics["matched_lithology_exact"]),
                ratio(metrics["document_boundary_exact"]),
                number(metrics["latency_seconds_per_document_wall"]),
                entry["paper_eligibility"],
            ]) + " |")
            continue
        if metrics.get("scope") == "authoritative-metadata controlled-degradation evaluation":
            for profile, values in metrics["profiles"].items():
                robustness_rows.append("| " + " | ".join([
                    entry["experiment_id"], run["model"], profile,
                    str(values["borehole_id_exact_match"]["numerator"]),
                    str(values["x_coordinate"]["x_coordinate_mae_coverage"]["numerator"]),
                    number(values["x_coordinate"]["x_coordinate_mae"]["value"]),
                    str(values["y_coordinate"]["y_coordinate_mae_coverage"]["numerator"]),
                    number(values["y_coordinate"]["y_coordinate_mae"]["value"]),
                    str(values["complete_three_field_exact"]["numerator"]),
                    str(values["field_omissions"]),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
        if metrics.get("scope") == "machine-adjudicated-silver-agreement evaluation":
            final_depth = metrics["borehole_fields"]["final_depth_m"]["final_depth_m_mae"]
            interval = metrics["intervals"]
            silver_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["document_count"]),
                ratio(metrics["borehole_fields"]["borehole_id"]),
                number(final_depth["value"]),
                number(interval["interval_precision"]["value"]),
                number(interval["interval_recall"]["value"]),
                number(interval["interval_f1"]["value"]),
                entry["paper_eligibility"],
            ]) + " |")
            continue
        if metrics.get("scope") == "source-disjoint authoritative-database interval transfer evaluation":
            interval = metrics["interval_metrics"]
            source_disjoint_transfer_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["document_count"]),
                str(metrics["content_group_count"]), str(metrics["reference_interval_count"]),
                str(metrics["predicted_interval_count"]), str(metrics["documents_with_predictions"]),
                number(interval["interval_precision"]["value"]),
                number(interval["interval_recall"]["value"]),
                number(interval["interval_f1"]["value"]),
                number(metrics["content_group_macro_interval_f1"]),
                ratio(metrics.get("document_full_exact")),
                (
                    "TBD" if metrics.get("ocr_resume_hit_count", 0)
                    else number(metrics["latency_seconds_per_document_wall"])
                ),
                entry["paper_eligibility"],
            ]) + " |")
            continue
        if metrics.get("scope") == "authoritative-interval benchmark evaluation":
            interval = metrics["interval_metrics"]
            rendered = "| " + " | ".join([
                entry["experiment_id"], run["model"], str(metrics["document_count"]),
                str(metrics["reference_interval_count"]),
                str(metrics["predicted_interval_count"]),
                number(interval["interval_precision"]["value"]),
                number(interval["interval_recall"]["value"]),
                number(interval["interval_f1"]["value"]),
                number(interval["matched_top_boundary_mae_m"]["value"]),
                number(interval["matched_bottom_boundary_mae_m"]["value"]),
                ratio(metrics.get("document_full_exact")),
                number(metrics["latency_seconds_per_document_wall"]),
                entry["paper_eligibility"],
            ]) + " |"
            if metrics.get("source_domain"):
                cross_source_interval_rows.append(rendered)
            elif entry["paper_eligibility"] == "formal_authoritative_interval":
                authoritative_interval_rows.append(rendered)
            elif entry["paper_eligibility"] == "development_authoritative_interval":
                development_interval_rows.append(rendered)
            else:
                conditional_interval_rows.append(rendered)
            continue
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
        elif metrics.get("ground_truth_tier") == "SYNTHETIC":
            interval = metrics["intervals"]
            final_depth = metrics["final_depth"]
            synthetic_rows.append("| " + " | ".join([
                entry["experiment_id"], run["model"],
                ratio(metrics["borehole_id_exact_match"]),
                ratio(final_depth["final_depth_m_mae_coverage"]),
                number(final_depth["final_depth_m_mae"]["value"]),
                number(interval["interval_precision"]["value"]),
                number(interval["interval_recall"]["value"]),
                number(interval["interval_f1"]["value"]),
                number(interval["matched_top_boundary_mae_m"]["value"]),
                number(metrics["latency_seconds_per_page"]),
                entry["paper_eligibility"],
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
        "### Synthetic controlled OCR results (not Real Gold)",
        "",
        "| Experiment | Model | Borehole ID EM | Final-depth coverage | Final-depth MAE (m) | Interval P | Interval R | Interval F1 | Matched top MAE (m) | s/page | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *synthetic_rows, "",
        "These rows use programmatically known Synthetic labels. They validate controlled extraction and robustness paths but cannot establish performance on Real Gold borehole logs.",
        "",
        "### Published manual-transcription Gold interval benchmark",
        "",
        "| Experiment | Model | Documents | Counties | Pages | Reference intervals | Predicted intervals | Documents with predictions | Interval P | Interval R | Interval F1 | Matched lithology exact | Boundary-exact documents | s/document | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *published_manual_gold_rows,
        "The reference intervals were manually transcribed verbatim by USGS staff from California DWR well-completion-report images and received published depth-sequence and completeness checks. The project did not repeat human review of the 60-document freeze. Metrics therefore evaluate against published manual transcription, while report-image redistribution remains a separate pre-submission check.",
        "",
        "### Held-out authoritative source-agreement interval result",
        "",
        "| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *authoritative_interval_rows,
        "The reference contains only interval boundaries from official database records whose complete sequence exactly agrees with an explicit table in the paired official PDF. The reported run is incremental and disjoint from parser-development records, but the source-agreement selection is not a representative random sample and no human annotation is claimed.",
        "",
        "### Source-disjoint official-database transfer agreement",
        "",
        "| Experiment | Model | Records | Visual content groups | Official intervals | Predicted intervals | Records with predictions | Interval P | Interval R | Interval F1 | Content-group macro F1 | Full-record exact | s/record | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *source_disjoint_transfer_rows,
        "These runs apply the frozen Thurgau parser without reference conditioning to all paired records in each successively frozen non-development-canton panel. Official database intervals belong to the same borehole objects, but complete page/database agreement was not established; the values therefore measure transfer agreement and combine extraction error with possible source mismatch. Content-group macro F1 prevents one repeated 21-page report from receiving eightfold weight. The indexed aggregations resumed completed OCR artifacts after earlier interrupted/metric-only runs, so end-to-end latency is not reported.",
        "",
        "### Cross-source authoritative interval diagnostic",
        "",
        "| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *cross_source_interval_rows,
        "This table adds a single official USGS Idaho PDF with an explicit generalized-lithology legend. It is a cross-source diagnostic, not evidence for a representative source-disjoint estimate; source rights remain pending manual verification.",
        "",
        "### Reference-conditioned interval diagnostics excluded from formal claims",
        "",
        "| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *conditional_interval_rows,
        "These retained runs conditioned candidate filtering/ranking on an official reference field and are diagnostics only. They are excluded from formal extraction claims even when their output metrics are otherwise valid.",
        "",
        "### Interval-parser development results excluded from held-out claims",
        "",
        "| Experiment | Model | Documents | Reference intervals | Predicted intervals | Interval P | Interval R | Interval F1 | Matched top MAE (m) | Matched bottom MAE (m) | Full-document exact | s/document | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *development_interval_rows,
        "These reference-independent runs used the v001 records on which parser/reread behavior was developed. They are retained as development evidence and excluded from the incremental held-out estimate.",
        "",
        "### Machine-adjudicated Silver agreement benchmark (not human accuracy)",
        "",
        "| Experiment | Model | Pages | Borehole ID agreement | Final-depth MAE (Silver) | Interval P | Interval R | Interval F1 | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *silver_rows,
        "These metrics measure agreement with an explicitly machine-adjudicated Silver reference. They are not human/expert accuracy, and the reference construction channels are recorded in the source ledger and experiment configuration.",
        "",
        "### Real-source controlled-degradation robustness (metadata fields only)",
        "",
        "| Experiment | Model | Profile | ID exact | X coverage | X MAE | Y coverage | Y MAE | Complete ID/X/Y | Field omissions | Eligibility |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *robustness_rows,
        "These rows use first-page borehole ID/X/Y references from official BGS metadata. Profiles are synthetic transformations of real scans; final depth, intervals, and lithology are excluded because the first-page scope does not provide those references.",
        "",
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
    comparison_rows = []
    source_protocol_rows = []
    source_qc_rows = []
    image_boundary_rows = []
    controlled_error_rows = []
    spatial_metadata_rows = []
    page_spatial_rows = []
    stratigraphic_layer_rows = []
    interoperability_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        if metrics.get("comparison") == "raw_vs_constrained_vs_synthetic_reference":
            for condition in metrics["conditions"]:
                comparison_rows.append("| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    number(condition["raw"]["mae_m"]["mean"], 6),
                    number(condition["constrained"]["mae_m"]["mean"], 6),
                    str(condition["accepted_corrections"]), str(condition["abstentions"]),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
        if metrics.get("comparison") in {
            "raw_vs_consensus_qc_vs_source_reference",
            "raw_vs_consensus_drop_vs_mean_fusion_vs_source_reference",
        }:
            for condition in metrics["conditions"]:
                fused = condition.get("mean_fusion")
                paired = condition.get("mean_fusion_vs_raw_paired")
                source_qc_rows.append("| " + " | ".join([
                    entry["experiment_id"], number(condition["magnitude_m"], 2),
                    f'{number(condition["raw"]["mae_m"]["mean"], 6)} ± {number(condition["raw"]["mae_m"]["std"], 6)}',
                    f'{number(condition["qc"]["mae_m"]["mean"], 6)} ± {number(condition["qc"]["mae_m"]["std"], 6)}',
                    (f'{number(fused["mae_m"]["mean"], 6)} ± {number(fused["mae_m"]["std"], 6)}' if fused else "TBD"),
                    (number(paired["relative_mae_reduction"]) if paired else "TBD"),
                    (f'{paired["fusion_better_count"]}/{paired["n"]}' if paired else "TBD"),
                    (f'{paired["two_sided_exact_sign_test_p"]:.3g}' if paired else "TBD"),
                    number(condition["coverage_mean"]),
                    str(condition["false_accepted_corruptions_total"]),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
        if (
            metrics.get("comparison") == "raw_image_boundary_vs_constraint_reread_boundary_vs_authoritative_reference_surface"
            and metrics.get("scope") != "real image-derived stratigraphic layer-model diagnostic"
        ):
            surface = metrics.get("surface") or metrics.get("aggregate", {})
            raw = surface.get("raw", {})
            final = surface.get("final", {})
            query_count = metrics.get("query_count")
            if query_count is None:
                query_count = raw.get("surface_query_count")
            image_boundary_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics.get("document_count", "TBD")),
                str(metrics.get("reference_point_count", "TBD")),
                str(query_count if query_count is not None else "TBD"),
                number(raw.get("boundary_mae_m")), number(final.get("boundary_mae_m")),
                number(raw.get("surface_error", {}).get("mae_m")),
                number(final.get("surface_error", {}).get("mae_m")),
                str(metrics.get("accepted_reread_count", "TBD")),
                str(metrics.get("needs_review_count", "TBD")),
                entry["paper_eligibility"],
            ]) + " |")
            continue
        if metrics.get("comparison") == "clean_authoritative_reference_vs_independently_injected_error_classes":
            for condition in metrics["conditions"]:
                controlled_error_rows.append("| " + " | ".join([
                    entry["experiment_id"], condition["error_type"],
                    str(condition["severity_index"]), number(condition["parameter"], 2),
                    condition["parameter_unit"],
                    f'{number(condition["boundary_mae_m"]["mean"], 6)} ± {number(condition["boundary_mae_m"]["std"], 6)}',
                    f'{number(condition["surface_error"]["mae_m"]["mean"], 6)} ± {number(condition["surface_error"]["mae_m"]["std"], 6)}',
                    number(condition["spatial_support_coverage"]["mean"], 4),
                    number(condition["topological_mismatch_document_rate"]["mean"], 4),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
        if metrics.get("comparison") == "page_explicit_spatial_values_vs_authoritative_database":
            spatial_metadata_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics["document_count"]),
                str(metrics["coordinate_prediction_count"]),
                ratio(metrics["coordinate_pair_coverage"]),
                ratio(metrics["coordinate_pair_exact_over_all"]),
                ratio(metrics["coordinate_pair_exact_when_predicted"]),
                number(metrics["x_error_m"]["mae"]),
                number(metrics["y_error_m"]["mae"]),
                str(metrics["page_database_coordinate_disagreement_count"]),
                str(metrics["collar_prediction_count"]),
                entry["paper_eligibility"],
            ]) + " |")
            continue
        if metrics.get("comparison") == "authoritative_reference_vs_page_coordinate_reference_boundary_vs_page_coordinate_raw_and_reread_boundary":
            for variant, values in metrics["variants"].items():
                page_spatial_rows.append("| " + " | ".join([
                    entry["experiment_id"], variant,
                    str(values["point_count"]), number(values["coverage"], 4),
                    number(values["boundary_mae_m"]),
                    number(values["surface_error"]["mae_m"]),
                    number(values["surface_error"]["rmse_m"]),
                    number(values["surface_error"]["max_abs_error_m"]),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
        if metrics.get("scope") == "real image-derived stratigraphic layer-model diagnostic":
            for variant, values in metrics.get("by_variant", {}).items():
                stratigraphic_layer_rows.append("| " + " | ".join([
                    entry["experiment_id"], variant, str(metrics.get("document_count", "TBD")),
                    str(metrics.get("layer_count", "TBD")),
                    number(values.get("mean_layer_thickness_mae_m")),
                    number(values.get("relative_absolute_volume_error")),
                    number(values.get("mean_top_boundary_support"), 4),
                    number(values.get("mean_bottom_boundary_support"), 4),
                    str(values.get("layers_with_negative_thickness", "TBD")),
                    entry["paper_eligibility"],
                ]) + " |")
            continue
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
        "### Executed Synthetic raw/constrained/reference comparison",
        "",
        "| Experiment | Injected boundary error (m) | Raw surface MAE (m) | Constrained surface MAE (m) | Accepted corrections | Abstentions | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---|",
        *comparison_rows, "",
        "This table executes the production constraint/rereading ranker and the same IDW surface for all inputs. It is controlled Synthetic algorithm evidence, not a real-site sensitivity estimate.",
        "",
        "### Real structured-source controlled raw/QC/reference comparison",
        "",
        "| Experiment | Injected error (m) | Raw MAE (m) | Consensus-drop MAE (m) | Mean-fusion MAE (m) | Relative reduction | Fusion better | Sign-test p | Retained coverage | False accepted | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *source_qc_rows, "",
        "This controlled experiment uses 602 real source records and post-decision source-reference scoring. It is not image-extraction accuracy or human Ground Truth. Consensus deletion changes interpolation support and can worsen the surface; support-preserving fusion is reported separately.",
        "",
        "### Real image-derived boundary to surface diagnostic",
        "",
        "| Experiment | Documents | Reference points | Query points | Raw boundary MAE (m) | Reread boundary MAE (m) | Raw surface MAE (m) | Reread surface MAE (m) | Accepted rereads | Needs review | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *image_boundary_rows, "",
        "This diagnostic inherits frozen reference-blinded image boundaries from the Paper II held-out run. Coordinates and collar elevations are taken from the authoritative structured record; image extraction of spatial metadata is not evaluated, so this is not a complete end-to-end spatial workflow.",
        "",
        "### Real stratigraphic layer-volume diagnostic",
        "",
        "| Experiment | Variant | Documents | Layers | Mean layer-thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Layers with negative thickness | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *stratigraphic_layer_rows, "",
        "These rows convert adjacent IDW contact surfaces into layer-thickness and volume estimates. They are real downstream diagnostics, not validated geological interpretations; sparse deep-layer support and authoritative collars/coordinates remain explicit limitations.",
        "",
        "### Authoritative controlled error-class propagation",
        "",
        "| Experiment | Error type | Severity | Parameter | Unit | Boundary MAE (m) | Surface MAE (m) | Support | Topology mismatch | Eligibility |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---|",
        *controlled_error_rows, "",
        "Each row aggregates 30 seeded injections on 35 held-out authoritative records and a fixed 1,265-query reference domain. Parameters are error-class specific and are not directly comparable across units. Coordinates and collar elevations are authoritative structured fields rather than image-derived predictions; no human Ground Truth is claimed.",
        "",
        "### External page spatial-metadata extraction",
        "",
        "| Experiment | Documents | Coordinate predictions | Coordinate coverage | Pair exact/all | Pair exact/predicted | X MAE (m) | Y MAE (m) | Page/database disagreements | Collar predictions | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *spatial_metadata_rows, "",
        "The frozen conservative parser was evaluated on every paired record outside the interval-v003 split. Database disagreement is not automatically attributed to recognition because the page and database can contain different values. Zero collar predictions is a measured abstention result, not missing evaluation output.",
        "",
        "### Page-coordinate downstream surface diagnostic",
        "",
        "| Experiment | Variant | Points | Coverage | Boundary MAE (m) | Surface MAE (m) | Surface RMSE (m) | Max error (m) | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *page_spatial_rows, "",
        "Page coordinates and frozen image-boundary predictions are reference-free, but every collar elevation remains supplied by the authoritative record because page extraction coverage was zero. The comparison is therefore a partial spatial workflow, not complete end-to-end extraction.",
        "",
        "### Licensed structured-source field proxy protocol",
        "",
        "| Experiment | Perturbation (m) | Seed | Repetitions/grid points | Proxy-surface MAE (m) | RMSE (m) | Max abs. error (m) | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *source_protocol_rows, "",
        "These rows use source-reported tabular values with origin-suppressed local coordinates. They are protocol-development evidence only, not image-derived automated extraction, a geological reference, constraint-QC, a true geological surface, absolute-location evidence, or formal downstream evidence. Multi-seed rows show mean ± sample standard deviation across seeds.",
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
    authoritative_rows = []
    interval_method_rows = []
    secondary_ablation_rows = []
    selective_rows = []
    california_sequence_rows = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        if metrics.get("comparison") == "single_pass_vs_constraint_guided_sequence_recovery":
            raw = metrics["raw_interval_metrics"]
            constrained = metrics["constrained_interval_metrics"]
            taxonomy = metrics["correction_taxonomy"]
            california_sequence_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics["document_count"]),
                str(metrics["county_count"]), str(metrics["reference_interval_count"]),
                str(metrics["candidate_count"]),
                number(raw["interval_precision"]["value"]),
                number(raw["interval_recall"]["value"]),
                number(raw["interval_f1"]["value"]),
                number(constrained["interval_precision"]["value"]),
                number(constrained["interval_recall"]["value"]),
                number(constrained["interval_f1"]["value"]),
                str(taxonomy["constrained_correct_added"]),
                str(taxonomy["constrained_incorrect_added"]),
                str(taxonomy["raw_correct_removed"]),
                ratio(metrics["false_correction_rate"]),
                entry["paper_eligibility"],
            ]) + " |")
        if metrics.get("scope") == "authoritative-metadata consensus/abstention evaluation":
            for field, values in metrics["by_field"].items():
                authoritative_rows.append("| " + " | ".join([
                    entry["experiment_id"], field, str(values["reference_count"]),
                    str(values["accepted_count"]), ratio({
                        "value": values["coverage"], "numerator": values["accepted_count"],
                        "denominator": values["reference_count"],
                    }),
                    number(values["accepted_accuracy"]),
                    str(values["review_count"]), number(values["manual_review_recall"]),
                    entry["paper_eligibility"],
                ]) + " |")
        if metrics.get("scope") == "authoritative-interval heldout constraint-rereading evaluation":
            first = metrics["first_pass"]["interval_metrics"]["interval_f1"]
            final = metrics["constraint_reread"]["interval_metrics"]["interval_f1"]
            interval_method_rows.append("| " + " | ".join([
                entry["experiment_id"], str(metrics["document_count"]),
                str(metrics["reference_interval_count"]), number(first["value"]),
                number(final["value"]), str(metrics["triggered_document_count"]),
                str(metrics["accepted_reread_count"]), str(metrics["needs_review_count"]),
                ratio(metrics["incorrect_document_trigger_recall"]),
                ratio(metrics["correct_document_trigger_rate"]),
                ratio(metrics["correction_success_rate"]),
                ratio(metrics["false_correction_rate"]),
                entry["paper_eligibility"],
            ]) + " |")
        if metrics.get("scope") == "secondary heldout component ablation on frozen v2 artifacts":
            for variant_name, values in metrics["variants"].items():
                interval = values["interval_metrics"]
                secondary_ablation_rows.append("| " + " | ".join([
                    entry["experiment_id"], variant_name,
                    number(interval["interval_precision"]["value"]),
                    number(interval["interval_recall"]["value"]),
                    number(interval["interval_f1"]["value"]),
                    f'{values["document_full_exact_count"]}/{metrics["document_count"]}',
                    str(values["changed_document_count"]),
                    entry["paper_eligibility"],
                ]) + " |")
        if metrics.get("scope") == "authoritative-interval selective-confidence secondary analysis":
            abstain = metrics["operational_policies"]["abstain_needs_review"]
            peer = metrics["operational_policies"]["require_peer_exact_agreement"]
            selective_rows.append("| " + " | ".join([
                entry["experiment_id"],
                number(metrics["brier_score"]),
                number(metrics["expected_calibration_error_5_bin"]),
                f'{abstain["accepted_documents"]}/{abstain["total_documents"]} ({abstain["coverage"]:.3f})',
                number(abstain["document_exact"]["value"]),
                number(abstain["interval_metrics"]["interval_f1"]["value"]),
                f'{peer["accepted_documents"]}/{peer["total_documents"]} ({peer["coverage"]:.3f})',
                number(peer["interval_metrics"]["interval_f1"]["value"]),
                entry["paper_eligibility"],
            ]) + " |")
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
        if entry.get("paper_eligibility") == "failure_analysis_only":
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
        "### Method and ablation results", "",
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "| Experiment | Variant | Disabled | Calibration n | Test n | Correction success | FCR | Review recall | Review rate | Auto-accept error | Raw ECE | Calibrated ECE | Eligibility |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *rows,
    ]
    if not rows:
        formal_section.append("| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | no formal run |")
    formal_section.extend(["",
        "Rows are generated from identical-case, one-module-at-a-time matrices. `formal_synthetic_method` rows are controlled Synthetic evidence and do not support human-GT claims; human-GT rows remain separately labelled.",
    ])
    return "\n".join([
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "### Real authoritative-metadata consensus and abstention", "",
        "| Experiment | Field | Reference n | Auto-accepted | Coverage | Accepted accuracy | Review | Review recall | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
        *authoritative_rows, "",
        "The decision policy accepts only equal non-null values from two independent OCR readers. References are consulted only after decisions are frozen. This is real metadata-field evidence; interval/lithology effects remain unmeasured.",
        "",
        "### Published manual-transcription Gold sequence recovery", "",
        "| Experiment | Documents | Counties | Reference intervals | Candidates | Raw P | Raw R | Raw F1 | Constrained P | Constrained R | Constrained F1 | Correct added | Incorrect added | Correct removed | FCR | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *california_sequence_rows, "",
        "The deterministic sequence ranker was frozen on the ten-document development partition and evaluated without reference access on the fifty-document California test. FCR counts both correct raw boundaries removed and incorrect constrained boundaries added. The result shows recovery gain and a non-negligible correction hazard rather than uniformly safe automatic repair.",
        "",
        "### Held-out authoritative-interval constraint-rereading result", "",
        "| Experiment | Documents | Reference intervals | First-pass F1 | Reread F1 | Triggered | Accepted rereads | Needs review | Incorrect-doc trigger recall | Correct-doc trigger rate | Correction success | FCR | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *interval_method_rows, "",
        "Each policy was frozen on its recorded development partition before the corresponding source-agreement test was evaluated. A null FCR means no automatic correction occurred; it is not zero. The same-source, explicit-table selection remains a major limitation.",
        "",
        "### Secondary held-out component analysis", "",
        "| Experiment | Variant | Interval P | Interval R | Interval F1 | Full-document exact | Changed documents vs v2 first pass | Eligibility |",
        "|---|---|---:|---:|---:|---:|---:|---|",
        *secondary_ablation_rows, "",
        "This component analysis was specified and executed after the full v2 held-out result was observed. It is descriptive evidence on frozen artifacts, not an independent confirmatory experiment; change counts for the legacy parser are parser differences, not automatic corrections.",
        "",
        "### Secondary selective-confidence and abstention analysis", "",
        "| Experiment | Brier | ECE (5-bin) | Abstain review coverage | Abstain document exact | Abstain interval F1 | Peer-agreement coverage | Peer-agreement interval F1 | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        *selective_rows, "",
        "The confidence lookup is fit on development-only outcomes and applied to held-out outputs. This table is a secondary post-result analysis with small denominators; it is not a confirmatory calibration estimate.",
        "",
        "### Public ROI engineering audit (no Ground Truth)", "",
        "| Experiment | Cases | VLM JSON-valid | VLM uncertain | OCR/VLM numeric-agreement cases | Accept proposals | Needs review | VLM s/ROI | Peak GiB | Eligibility |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *audit_rows, "",
        "These rows report parser, candidate-path, latency, and resource behavior only. Source annotations are `auto`; accuracy, correction success, and FCR are undefined.",
        "", *formal_section,
    ]) + "\n"
