import copy
import json

import pytest

from geologparser.annotation import create_annotation
from geologparser.annotation_export import (
    annotation_agreement, export_verified_annotations, ground_truth_gate,
)


def record(root):
    return json.loads((root / "examples/boreholes/synthetic_valid.json").read_text())


def test_verified_export_rejects_auto_and_accepts_human(tmp_path, request):
    root = request.config.rootpath
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    auto = create_annotation("A", {"panel_id": "A"}, record(root), "AUTO", "auto")
    (annotations / "A.json").write_text(json.dumps(auto))
    with pytest.raises(ValueError, match="Ground Truth gate"):
        export_verified_annotations(annotations, tmp_path / "gt.jsonl")
    human = create_annotation("A", {"panel_id": "A"}, record(root), "annotator-1", "single_verified")
    (annotations / "A.json").write_text(json.dumps(human))
    result = export_verified_annotations(annotations, tmp_path / "gt.jsonl")
    assert result["annotation_count"] == 1
    assert len(result["sha256"]) == 64


def test_ground_truth_gate_rejects_status_only_and_empty_intervals(request):
    root = request.config.rootpath
    source = record(root)
    source["intervals"] = []
    annotation = create_annotation("A", {"panel_id": "A"}, source, "reviewer", "single_verified")
    assert "NO_INTERVALS" in ground_truth_gate(annotation)
    assert ground_truth_gate(annotation, require_intervals=False) == []


def test_ground_truth_gate_requires_populated_interval_fields_to_be_human_confirmed(request):
    root = request.config.rootpath
    annotation = create_annotation("A", {"panel_id": "A"}, record(root), "reviewer", "single_verified")
    annotation["record"]["intervals"][0]["top_depth_m"]["extraction_method"] = "vlm"
    failures = ground_truth_gate(annotation)
    assert "FIELD_NOT_HUMAN_AUTHORED:intervals[0].top_depth_m" in failures


def test_ground_truth_gate_accepts_human_confirmed_null_as_absent_source_field(request):
    root = request.config.rootpath
    annotation = create_annotation("A", {"panel_id": "A"}, record(root), "reviewer", "single_verified")
    field = annotation["record"]["intervals"][0]["description_raw"]
    field.update({
        "value": None, "source_page": 1, "extraction_method": "human",
        "validation_status": "human_verified",
    })
    assert ground_truth_gate(annotation) == []


def test_ground_truth_gate_rejects_unreviewed_null_borehole_field(request):
    root = request.config.rootpath
    annotation = create_annotation("A", {"panel_id": "A"}, record(root), "reviewer", "single_verified")
    field = annotation["record"]["borehole"]["groundwater_depth_m"]
    field.update({
        "value": None, "source_page": None, "extraction_method": "vlm",
        "validation_status": "needs_review",
    })
    failures = ground_truth_gate(annotation)
    assert "FIELD_NOT_HUMAN_VERIFIED:borehole.groundwater_depth_m" in failures
    assert "FIELD_NOT_HUMAN_AUTHORED:borehole.groundwater_depth_m" in failures
    assert "MISSING_SOURCE_PAGE:borehole.groundwater_depth_m" in failures


def test_ground_truth_gate_accepts_human_confirmed_null_borehole_field(request):
    root = request.config.rootpath
    annotation = create_annotation("A", {"panel_id": "A"}, record(root), "reviewer", "single_verified")
    field = annotation["record"]["borehole"]["groundwater_depth_m"]
    field.update({
        "value": None, "source_page": 1, "extraction_method": "human",
        "validation_status": "human_verified",
    })
    assert ground_truth_gate(annotation) == []


def test_annotation_agreement_reports_numeric_difference(request):
    root = request.config.rootpath
    first = create_annotation("A", {"panel_id": "A"}, record(root), "one", "single_verified")
    changed = copy.deepcopy(first["record"])
    changed["intervals"][0]["bottom_depth_m"]["value"] += 0.1
    second = create_annotation("A", {"panel_id": "A"}, changed, "two", "double_verified")
    result = annotation_agreement([first], [second])
    assert result["document_count"] == 1
    assert result["boundary"]["boundary_agreement_mae_m"]["value"] > 0
