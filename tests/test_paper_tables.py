import json
from pathlib import Path

from geologparser.paper_artifacts import paper1_table, paper2_table, paper3_table


def write_run(root: Path, metrics: dict, run: dict):
    path = root / "result"
    path.mkdir()
    (path / "metrics.json").write_text(json.dumps(metrics))
    (path / "run.json").write_text(json.dumps(run))
    return path


def test_paper1_table_marks_null_metric_tbd(tmp_path: Path, monkeypatch):
    metrics = {
        "borehole_id_exact_match": {"value": 0.5, "numerator": 1, "denominator": 2},
        "x_coordinate": {
            "x_coordinate_mae_coverage": {"value": 0, "numerator": 0, "denominator": 2},
            "x_coordinate_mae": {"value": None},
        },
        "final_depth": {"final_depth_mae_m_coverage": {"value": 0, "numerator": 0, "denominator": 2}},
        "total_intervals_emitted": 0, "latency_seconds_per_page": 1.2,
    }
    write_run(tmp_path, metrics, {"model": "test"})
    table = paper1_table([{"experiment_id": "E", "result_path": "result", "paper_eligibility": "audit"}], tmp_path)
    assert "TBD" in table
    assert "0/2 (0.000)" in table


def test_paper1_table_separates_no_gt_privacy_minimized_ocr_coverage(tmp_path: Path):
    metrics = {
        "record_output_policy": "hash_and_presence_only",
        "selected_items": 28, "completed_items": 28,
        "items_with_borehole_id": 27, "items_with_final_depth": 0,
        "items_with_any_interval": 2, "emitted_intervals": 2,
        "ocr_regions": 1528, "constraint_evaluations": 14,
        "constraint_violations": 4, "latency_mean_seconds_per_item": 1.64,
        "accuracy_metrics": None, "human_ground_truth_count": 0,
    }
    write_run(tmp_path, metrics, {"model": "privacy-minimized-test"})
    table = paper1_table([{
        "experiment_id": "P1_COVERAGE", "result_path": "result",
        "paper_eligibility": "audit_only",
    }], tmp_path)
    assert "Privacy-minimized OCR coverage audits" in table
    assert "P1_COVERAGE" in table
    assert "27/28" in table
    assert "coverage diagnostics, not accuracy estimates" in table


def test_paper1_table_separates_privacy_minimized_native_pdf_coverage(tmp_path: Path):
    metrics = {
        "record_output_policy": "hash_and_presence_only",
        "coverage_channels": ["direct_text_regex", "positioned_text_layout"],
        "selected_items": 18, "completed_items": 18, "text_regions": 120,
        "regex_items_with_borehole_id": 0, "regex_items_with_any_interval": 0,
        "regex_emitted_intervals": 0, "layout_items_with_any_interval": 4,
        "layout_emitted_intervals": 12, "layout_constraint_evaluations": 84,
        "layout_constraint_violations": 3, "latency_mean_seconds_per_item": 0.1,
        "accuracy_metrics": None, "human_ground_truth_count": 0,
    }
    write_run(tmp_path, metrics, {"model": "native-privacy-minimized-test"})
    table = paper1_table([{
        "experiment_id": "P1_NATIVE", "result_path": "result",
        "paper_eligibility": "audit_only",
    }], tmp_path)
    assert "Privacy-minimized native-PDF coverage audits" in table
    assert "P1_NATIVE" in table
    assert "4/18" in table
    assert "source text, extracted values, and source bboxes are omitted" in table


def test_paper1_table_separates_synthetic_controlled_results(tmp_path: Path):
    metric = lambda value, numerator=1, denominator=1: {
        "value": value, "numerator": numerator, "denominator": denominator,
    }
    metrics = {
        "ground_truth_tier": "SYNTHETIC",
        "borehole_id_exact_match": metric(0.5, 1, 2),
        "final_depth": {
            "final_depth_m_mae_coverage": metric(1.0, 2, 2),
            "final_depth_m_mae": metric(0.0, 0, 2),
        },
        "intervals": {
            "interval_precision": metric(1.0), "interval_recall": metric(0.5),
            "interval_f1": metric(2 / 3), "matched_top_boundary_mae_m": metric(0.0),
        },
        "latency_seconds_per_page": 0.4,
    }
    write_run(tmp_path, metrics, {"model": "synthetic-test"})
    table = paper1_table([{
        "experiment_id": "P1_SYNTH", "result_path": "result",
        "paper_eligibility": "audit_only",
    }], tmp_path)
    assert "Synthetic controlled OCR results (not Real Gold)" in table
    assert "P1_SYNTH" in table
    assert "cannot establish performance on Real Gold" in table


def test_paper1_table_includes_heldout_authoritative_interval_with_scope_warning(tmp_path: Path):
    metric = lambda value, numerator=1, denominator=1: {
        "value": value, "numerator": numerator, "denominator": denominator,
    }
    metrics = {
        "scope": "authoritative-interval benchmark evaluation",
        "document_count": 9,
        "reference_interval_count": 21,
        "predicted_interval_count": 15,
        "document_full_exact": metric(2 / 3, 6, 9),
        "interval_metrics": {
            "interval_precision": metric(1.0, 15, 15),
            "interval_recall": metric(15 / 21, 15, 21),
            "interval_f1": metric(5 / 6),
            "matched_top_boundary_mae_m": metric(0.0, 0, 15),
            "matched_bottom_boundary_mae_m": metric(0.0, 0, 15),
        },
        "latency_seconds_per_document_wall": 3.1,
    }
    write_run(tmp_path, metrics, {"model": "tesseract-pilot"})
    table = paper1_table([{
        "experiment_id": "P1_AUTH_INTERVAL", "result_path": "result",
        "paper_eligibility": "formal_authoritative_interval",
    }], tmp_path)
    assert "Held-out authoritative source-agreement interval result" in table
    assert "P1_AUTH_INTERVAL" in table
    assert "15 | 1.000 | 0.714 | 0.833" in table
    assert "not a representative random sample" in table
    assert "no human annotation is claimed" in table


def test_paper3_table_is_labelled_protocol_only(tmp_path: Path, monkeypatch):
    metrics = {"conditions": [{"magnitude_m": .1, "seed": 1, "count": 3, "mae_m": .02, "rmse_m": .03, "max_abs_error_m": .04}]}
    write_run(tmp_path, metrics, {})
    table = paper3_table([{"experiment_id": "E", "result_path": "result", "paper_eligibility": "protocol_only"}], tmp_path)
    assert "protocol_only" in table
    assert "not evidence" in table


def test_paper3_table_includes_hash_traceable_pyvista_interop(tmp_path: Path):
    metrics = {
        "point_count": 9, "triangle_cell_count": 8,
        "bounds": [0, 1, 0, 1, 98, 100],
        "surface_vtp_sha256": "a" * 64, "surface_png_sha256": "b" * 64,
    }
    write_run(tmp_path, metrics, {})
    table = paper3_table([{
        "experiment_id": "P3_INTEROP", "result_path": "result",
        "paper_eligibility": "protocol_only",
    }], tmp_path)
    assert "Synthetic 3D interoperability" in table
    assert "P3_INTEROP" in table
    assert "a" * 64 in table


def test_paper3_table_separates_structured_source_from_synthetic(tmp_path: Path):
    metrics = {
        "data_status": "licensed_source_structured_data_pending_human_spatial_review",
        "conditions": [{
            "magnitude_m": 1.0, "repetitions": 30,
            "mae_m": {"mean": 0.2, "std": 0.01},
            "rmse_m": {"mean": 0.3, "std": 0.02},
            "max_abs_error_m": {"mean": 0.9, "std": 0.03},
        }],
    }
    write_run(tmp_path, metrics, {})
    table = paper3_table([{
        "experiment_id": "P3_SOURCE", "result_path": "result",
        "paper_eligibility": "protocol_only",
    }], tmp_path)
    synthetic_section, source_section = table.split(
        "### Licensed structured-source field proxy protocol"
    )
    assert "P3_SOURCE" not in synthetic_section
    assert "P3_SOURCE" in source_section
    assert "not image-derived automated extraction" in source_section


def test_paper3_table_includes_controlled_error_classes(tmp_path: Path):
    metrics = {
        "comparison": "clean_authoritative_reference_vs_independently_injected_error_classes",
        "conditions": [{
            "error_type": "missing_boundary", "severity_index": 2,
            "parameter": .25, "parameter_unit": "affected_document_fraction",
            "boundary_mae_m": {"mean": 0.0, "std": 0.0},
            "surface_error": {"mae_m": {"mean": 4.28, "std": .5}},
            "spatial_support_coverage": {"mean": .8875},
            "topological_mismatch_document_rate": {"mean": .2571},
        }],
    }
    write_run(tmp_path, metrics, {})
    table = paper3_table([{
        "experiment_id": "P3_CLASSES", "result_path": "result",
        "paper_eligibility": "formal_authoritative_controlled_error_downstream",
    }], tmp_path)
    assert "Authoritative controlled error-class propagation" in table
    assert "missing_boundary" in table
    assert "4.280000" in table
    assert "not directly comparable across units" in table


def test_paper3_table_includes_spatial_metadata_and_partial_surface(tmp_path: Path):
    spatial = tmp_path / "spatial"
    surface = tmp_path / "surface"
    spatial.mkdir(); surface.mkdir()
    (spatial / "metrics.json").write_text(json.dumps({
        "comparison": "page_explicit_spatial_values_vs_authoritative_database",
        "document_count": 88, "coordinate_prediction_count": 53,
        "coordinate_pair_coverage": {"value": 53/88, "numerator": 53, "denominator": 88},
        "coordinate_pair_exact_over_all": {"value": 51/88, "numerator": 51, "denominator": 88},
        "coordinate_pair_exact_when_predicted": {"value": 51/53, "numerator": 51, "denominator": 53},
        "x_error_m": {"mae": 94.45}, "y_error_m": {"mae": 132.08},
        "page_database_coordinate_disagreement_count": 2, "collar_prediction_count": 0,
    }))
    (surface / "metrics.json").write_text(json.dumps({
        "comparison": "authoritative_reference_vs_page_coordinate_reference_boundary_vs_page_coordinate_raw_and_reread_boundary",
        "variants": {"page_coordinate_reference_boundary": {
            "point_count": 17, "coverage": 17/35, "boundary_mae_m": 0,
            "surface_error": {"mae_m": 9.514, "rmse_m": 13.75, "max_abs_error_m": 69.82},
        }},
    }))
    entries = [
        {"experiment_id": "SPATIAL", "result_path": "spatial", "paper_eligibility": "formal_authoritative_spatial_extraction"},
        {"experiment_id": "SURFACE", "result_path": "surface", "paper_eligibility": "formal_partial_page_spatial_downstream"},
    ]
    table = paper3_table(entries, tmp_path)
    assert "External page spatial-metadata extraction" in table
    assert "51/53 (0.962)" in table
    assert "Page-coordinate downstream surface diagnostic" in table
    assert "9.514" in table
    assert "partial spatial workflow" in table


def test_paper2_table_uses_gated_ablation_metrics(tmp_path: Path):
    metric = lambda value: {"value": value, "numerator": value, "denominator": 1}
    metrics = {
        "protocol": "paper2_one_module_ablation_matrix_v001",
        "variants": {"full": {"disabled_modules": [], "metrics": {
            "calibration_case_count": 2, "test_case_count": 3,
            "correction": {"correction_success_rate": metric(1), "false_correction_rate": metric(0)},
            "review": {
                "manual_review_recall": metric(1), "review_rate": metric(.5),
                "auto_accept_error_rate": metric(.25),
            },
            "confidence": {
                "raw_expected_calibration_error": metric(.2),
                "calibrated_expected_calibration_error": metric(.1),
            },
        }}},
    }
    write_run(tmp_path, metrics, {})
    table = paper2_table([{"experiment_id": "P2", "result_path": "result", "paper_eligibility": "formal"}], tmp_path)
    assert "full" in table
    assert "Auto-accept error" in table
    assert "human-GT rows remain separately labelled" in table


def test_paper2_table_separates_roi_audit_from_formal_results(tmp_path: Path):
    metrics = {
        "case_count": 2, "vlm_schema_valid_count": 2, "vlm_uncertain_count": 0,
        "cross_reader_numeric_agreement_case_count": 2,
        "accept_proposal_count": 0, "needs_review_count": 2,
        "vlm_latency_mean_seconds_per_roi": 3.5,
        "peak_gpu_memory_bytes": 9 * 1024**3,
    }
    write_run(tmp_path, metrics, {})
    table = paper2_table([{
        "experiment_id": "P2_ROI", "result_path": "result", "paper_eligibility": "audit_only",
    }], tmp_path)
    assert "Public ROI engineering audit" in table
    assert "P2_ROI" in table
    assert "accuracy, correction success, and FCR are undefined" in table
    assert "no formal run" in table


def test_paper2_table_reports_heldout_interval_negative_result_without_zero_fcr(tmp_path: Path):
    metric = lambda value, numerator, denominator: {
        "value": value, "numerator": numerator, "denominator": denominator,
    }
    metrics = {
        "scope": "authoritative-interval heldout constraint-rereading evaluation",
        "document_count": 20,
        "reference_interval_count": 55,
        "first_pass": {"interval_metrics": {"interval_f1": metric(.8545, .8545, 1)}},
        "constraint_reread": {"interval_metrics": {"interval_f1": metric(.8545, .8545, 1)}},
        "triggered_document_count": 1,
        "accepted_reread_count": 0,
        "needs_review_count": 1,
        "incorrect_document_trigger_recall": metric(0.0, 0, 3),
        "correct_document_trigger_rate": metric(1 / 17, 1, 17),
        "correction_success_rate": metric(None, 0, 0),
        "false_correction_rate": metric(None, 0, 0),
    }
    write_run(tmp_path, metrics, {})
    table = paper2_table([{
        "experiment_id": "P2_HELDOUT", "result_path": "result",
        "paper_eligibility": "formal_authoritative_interval_method",
    }], tmp_path)
    assert "Held-out authoritative-interval" in table
    assert "P2_HELDOUT" in table
    assert "0/3 (0.000)" in table
    assert "TBD" in table
    assert "null FCR means no automatic correction occurred" in table


def test_paper2_table_labels_secondary_component_ablation_as_descriptive(tmp_path: Path):
    metric = lambda value: {"value": value, "numerator": value, "denominator": 1}
    metrics = {
        "scope": "secondary heldout component ablation on frozen v2 artifacts",
        "document_count": 35,
        "variants": {
            "v2_first_pass": {
                "interval_metrics": {
                    "interval_precision": metric(.892),
                    "interval_recall": metric(.825),
                    "interval_f1": metric(.857),
                },
                "document_full_exact_count": 25,
                "changed_document_count": 0,
            },
            "full_v2": {
                "interval_metrics": {
                    "interval_precision": metric(.972),
                    "interval_recall": metric(.875),
                    "interval_f1": metric(.921),
                },
                "document_full_exact_count": 29,
                "changed_document_count": 4,
            },
        },
    }
    write_run(tmp_path, metrics, {})
    table = paper2_table([{
        "experiment_id": "P2_SECONDARY", "result_path": "result",
        "paper_eligibility": "secondary_ablation_only",
    }], tmp_path)
    assert "Secondary held-out component analysis" in table
    assert "P2_SECONDARY" in table
    assert "29/35" in table
    assert "not an independent confirmatory experiment" in table
