import copy
import json
from pathlib import Path

import pytest

from geologparser.annotation_proposals import proposal_from_prediction


ROOT = Path(__file__).resolve().parents[1]


def test_proposal_keeps_auto_status_and_experiment_lineage():
    record = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text())
    record["document"]["document_id"] = "PANEL"
    record["intervals"][0]["top_depth_m"]["source_bbox"] = [10, 20, 30, 40]
    record["intervals"][0]["top_depth_m"]["display_bbox"] = None
    prediction = {"item_id": "PANEL", "record": record}
    panel = {
        "panel_id": "PANEL", "source_page": 1,
        "source_pdf_rotation_matrix": [1, 0, 0, 1, 0, 0],
        "visual_clip_points": [0, 0, 100, 100],
        "rendered_width_px": 200, "rendered_height_px": 200,
    }
    proposal = proposal_from_prediction(prediction, panel, "EXP_001")
    assert proposal["annotation_status"] == "auto"
    assert proposal["annotator_id"] == "AUTO_EXPERIMENT:EXP_001"
    assert proposal["record"]["document"]["metadata"]["annotation_proposal_experiment_id"] == "EXP_001"
    assert proposal["record"]["intervals"][0]["top_depth_m"]["display_bbox"] is not None


def test_proposal_rejects_mismatched_panel_identity():
    record = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text())
    with pytest.raises(ValueError, match="item_id"):
        proposal_from_prediction({"item_id": "A", "record": copy.deepcopy(record)}, {"panel_id": "B"}, "E")
