import copy
import json

import pytest

from geologparser.annotation import create_annotation
from geologparser.annotation_export import annotation_agreement, export_verified_annotations


def record(root):
    return json.loads((root / "examples/boreholes/synthetic_valid.json").read_text())


def test_verified_export_rejects_auto_and_accepts_human(tmp_path, request):
    root = request.config.rootpath
    annotations = tmp_path / "annotations"
    annotations.mkdir()
    auto = create_annotation("A", {"panel_id": "A"}, record(root), "AUTO", "auto")
    (annotations / "A.json").write_text(json.dumps(auto))
    with pytest.raises(ValueError, match="not human-verified"):
        export_verified_annotations(annotations, tmp_path / "gt.jsonl")
    human = create_annotation("A", {"panel_id": "A"}, record(root), "annotator-1", "single_verified")
    (annotations / "A.json").write_text(json.dumps(human))
    result = export_verified_annotations(annotations, tmp_path / "gt.jsonl")
    assert result["annotation_count"] == 1
    assert len(result["sha256"]) == 64


def test_annotation_agreement_reports_numeric_difference(request):
    root = request.config.rootpath
    first = create_annotation("A", {"panel_id": "A"}, record(root), "one", "single_verified")
    changed = copy.deepcopy(first["record"])
    changed["intervals"][0]["bottom_depth_m"]["value"] += 0.1
    second = create_annotation("A", {"panel_id": "A"}, changed, "two", "double_verified")
    result = annotation_agreement([first], [second])
    assert result["document_count"] == 1
    assert result["boundary"]["boundary_agreement_mae_m"]["value"] > 0
