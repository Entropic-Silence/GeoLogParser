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
    assert "human-GT-gated" in table
