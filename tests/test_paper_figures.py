import json
from pathlib import Path

from geologparser.paper_figures import (
    save_degradation_profiles,
    save_error_propagation,
    save_method_schematic,
    save_padova_locations,
    save_source_field_propagation,
)


def test_paper_figure_writers_create_nonempty_files(tmp_path: Path):
    degradation = tmp_path / "degradation.jsonl"
    degradation.write_text("\n".join([
        json.dumps({"profile": "blur_1"}), json.dumps({"profile": "blur_1"}),
        json.dumps({"profile": "noise_1"}),
    ]) + "\n")
    locations = tmp_path / "locations.jsonl"
    locations.write_text("\n".join([
        json.dumps({"link_key": "GS1", "longitude": 10, "latitude": 44}),
        json.dumps({"link_key": "PS1", "longitude": 11, "latitude": 44.5}),
        json.dumps({"link_key": "TS2", "longitude": 13, "latitude": 45.5}),
    ]) + "\n")
    outputs = [tmp_path / "d.png", tmp_path / "l.png", tmp_path / "m.png"]
    save_degradation_profiles(degradation, outputs[0])
    save_padova_locations(locations, outputs[1])
    save_method_schematic(outputs[2])
    assert all(path.stat().st_size > 1000 for path in outputs)


def test_propagation_figures_separate_synthetic_and_structured_source(tmp_path: Path):
    synthetic = tmp_path / "synthetic"
    source = tmp_path / "source"
    synthetic.mkdir()
    source.mkdir()
    condition = {
        "magnitude_m": 1.0,
        "mae_m": {"mean": 0.5, "std": 0.1},
    }
    (synthetic / "metrics.json").write_text(json.dumps({"conditions": [condition]}))
    (source / "metrics.json").write_text(json.dumps({
        "data_status": "licensed_source_structured_data_pending_human_spatial_review",
        "source_record_count": 602,
        "conditions": [condition],
    }))
    entries = [
        {"experiment_id": "SYNTH", "result_path": "synthetic"},
        {"experiment_id": "SOURCE", "result_path": "source"},
    ]
    synthetic_output = tmp_path / "synthetic.png"
    source_output = tmp_path / "source.png"
    save_error_propagation(entries, tmp_path, synthetic_output)
    save_source_field_propagation(entries, tmp_path, source_output)
    assert synthetic_output.stat().st_size > 1000
    assert source_output.stat().st_size > 1000
