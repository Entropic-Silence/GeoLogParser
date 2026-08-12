import json
from pathlib import Path

from geologparser.paper_artifacts import paper1_table, paper3_table


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
