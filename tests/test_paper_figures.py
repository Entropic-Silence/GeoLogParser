import json
from pathlib import Path

from geologparser.paper_figures import (
    save_degradation_profiles,
    save_error_propagation,
    save_image_boundary_surface,
    save_image_multiboundary_surface,
    save_controlled_error_class_propagation,
    save_page_spatial_surface,
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


def test_image_boundary_surface_figure(tmp_path: Path):
    result = tmp_path / "image"
    result.mkdir()
    (result / "metrics.json").write_text(json.dumps({
        "comparison": "raw_image_boundary_vs_constraint_reread_boundary_vs_authoritative_reference_surface",
        "document_count": 35,
        "query_count": 10,
        "surface": {
            "raw": {"boundary_mae_m": 1.4, "surface_error": {"mae_m": 3.4}},
            "final": {"boundary_mae_m": 0.9, "surface_error": {"mae_m": 3.0}},
        },
    }))
    output = tmp_path / "image.png"
    save_image_boundary_surface([{"experiment_id": "IMAGE", "result_path": "image"}], tmp_path, output)
    assert output.stat().st_size > 1000


def test_image_multiboundary_surface_figure(tmp_path: Path):
    result = tmp_path / "multi"
    result.mkdir()
    (result / "metrics.json").write_text(json.dumps({
        "scope": "real image-derived multi-boundary downstream surface diagnostic",
        "per_boundary": [
            {"boundary_index": 1, "variants": {
                "raw": {"coverage": .9, "surface_error": {"mae_m": 3.4}},
                "final": {"coverage": .95, "surface_error": {"mae_m": 3.0}},
            }},
            {"boundary_index": 2, "variants": {
                "raw": {"coverage": .6, "surface_error": {"mae_m": 20.0}},
                "final": {"coverage": .7, "surface_error": {"mae_m": 18.0}},
            }},
        ],
    }))
    output = tmp_path / "multi.png"
    save_image_multiboundary_surface([{"experiment_id": "MULTI", "result_path": "multi"}], tmp_path, output)
    assert output.stat().st_size > 1000


def test_controlled_error_class_figure(tmp_path: Path):
    result = tmp_path / "classes"
    result.mkdir()
    conditions = []
    for error_type in (
        "boundary_shift", "coordinate_shift", "missing_boundary",
        "merged_layer", "split_layer", "duplicate_boundary",
    ):
        for severity in (1, 2, 3):
            conditions.append({
                "error_type": error_type, "severity_index": severity,
                "parameter": severity * (10 if error_type == "coordinate_shift" else .1),
                "parameter_unit": "m" if error_type in {"boundary_shift", "coordinate_shift"} else "affected_document_fraction",
                "surface_error": {"mae_m": {"mean": severity * .5}},
                "spatial_support_coverage": {"mean": 1 - severity * .05},
                "topological_mismatch_document_rate": {"mean": severity * .1},
            })
    (result / "metrics.json").write_text(json.dumps({
        "scope": "authoritative controlled multi-error downstream propagation evaluation",
        "conditions": conditions,
    }))
    output = tmp_path / "classes.png"
    save_controlled_error_class_propagation(
        [{"experiment_id": "CLASSES", "result_path": "classes"}], tmp_path, output,
    )
    assert output.stat().st_size > 1000


def test_page_spatial_surface_figure(tmp_path: Path):
    result = tmp_path / "page-spatial"
    result.mkdir()
    variants = {
        "page_coordinate_reference_boundary": {"coverage": .49, "surface_error": {"mae_m": 9.5}},
        "page_coordinate_raw_boundary": {"coverage": .49, "surface_error": {"mae_m": 9.5}},
        "page_coordinate_reread_boundary": {"coverage": .49, "surface_error": {"mae_m": 9.5}},
        "authoritative_coordinate_reread_boundary": {"coverage": .97, "surface_error": {"mae_m": 3.05}},
    }
    (result / "metrics.json").write_text(json.dumps({
        "scope": "real page-coordinate image-boundary downstream surface diagnostic",
        "variants": variants,
    }))
    output = tmp_path / "page-spatial.png"
    save_page_spatial_surface(
        [{"experiment_id": "PAGE", "result_path": "page-spatial"}], tmp_path, output,
    )
    assert output.stat().st_size > 1000
