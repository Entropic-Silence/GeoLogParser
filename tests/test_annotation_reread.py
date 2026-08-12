import json
from pathlib import Path

import pytest

from geologparser.annotation_reread import resolve_reread_bbox, run_annotation_reread
from geologparser.ocr import TextRegion


ROOT = Path(__file__).resolve().parents[1]


class FakeAdapter:
    name = "fake_ocr"

    def extract(self, _path):
        return [TextRegion(1, (0, 0, 20, 10), "1.20", 0.99, "ocr")]


def annotation(tmp_path: Path):
    from PIL import Image
    image = tmp_path / "panel.png"
    Image.new("RGB", (300, 120), "white").save(image)
    record = json.loads(
        (ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8")
    )
    record["intervals"][1]["top_depth_m"].update({
        "value": 1.5, "display_bbox": [20, 20, 90, 60],
    })
    return {
        "annotation_id": "test-panel", "revision": 4,
        "panel": {"rendered_path": str(image)}, "record": record,
    }


def test_annotation_reread_persists_non_mutating_evidence(tmp_path):
    value = annotation(tmp_path)
    original = json.dumps(value["record"], sort_keys=True)
    result = run_annotation_reread(
        value, "intervals[1].top_depth_m", [FakeAdapter()], tmp_path / "runs",
        padding_pixels=0, scale=1,
    )
    assert result["decision"]["status"] == "ACCEPT_PROPOSAL"
    assert result["decision"]["accepted_value"] == 1.2
    assert result["decision"]["proposed_record"]["intervals"][1]["top_depth_m"]["validation_status"] == "needs_review"
    assert result["interpretation"].startswith("non-mutating")
    run = tmp_path / "runs/test-panel" / result["run_id"]
    assert (run / "roi.png").is_file()
    assert (run / "result.json").is_file()
    assert len(result["result_sha256"]) == 64
    assert json.dumps(value["record"], sort_keys=True) == original


def test_bbox_resolution_refuses_unmapped_pdf_coordinates(tmp_path):
    value = annotation(tmp_path)
    envelope = value["record"]["intervals"][1]["top_depth_m"]
    envelope.pop("display_bbox")
    envelope["source_bbox"] = [1, 2, 3, 4]
    value["record"]["document"]["bbox_coordinate_space"] = "pdf_points"
    with pytest.raises(ValueError, match="rendered-pixel"):
        resolve_reread_bbox(value["record"], "intervals[1].top_depth_m", None)


def test_bbox_resolution_rejects_non_numeric_field(tmp_path):
    value = annotation(tmp_path)
    with pytest.raises(ValueError, match="numeric MVP"):
        resolve_reread_bbox(value["record"], "intervals[1].lithology_raw", [1, 2, 3, 4])
