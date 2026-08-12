import copy
import json
from pathlib import Path

import pytest

from geologparser.annotation import create_annotation
from geologparser.evaluation import evaluate_benchmark


ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    reference = json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text())
    annotation = create_annotation("PANEL", {"panel_id": "PANEL"}, reference, "H1", "single_verified")
    prediction = copy.deepcopy(reference)
    prediction["document"]["document_id"] = "PANEL"
    return annotation, {"item_id": "PANEL", "record": prediction}


def test_benchmark_evaluation_reports_real_denominators_and_errors():
    reference, prediction = fixtures()
    prediction["record"]["borehole"]["final_depth_m"]["value"] = 4.6
    prediction["record"]["intervals"][0]["lithology_raw"]["value"] = "细砂"
    metrics, errors = evaluate_benchmark(
        [reference], [prediction], critical_error_thresholds={"final_depth_m": 0.05},
    )
    assert metrics["document_count"] == 1
    assert metrics["borehole_fields"]["final_depth_m"]["final_depth_m_mae"]["value"] == pytest.approx(0.1)
    assert metrics["intervals"]["interval_f1"]["value"] == 1
    assert metrics["intervals"]["lithology_raw_exact_match"]["value"] < 1
    assert metrics["borehole_fields"]["final_depth_m"]["critical_numerical_error_rate"]["value"] == 1
    assert metrics["text"]["description_normalized_edit_similarity"]["value"] == 1
    assert any(item["error_type"] == "lithology_semantic_error" for item in errors)


def test_benchmark_evaluation_rejects_auto_gt_and_id_mismatch():
    reference, prediction = fixtures()
    reference["annotation_status"] = "auto"
    with pytest.raises(ValueError, match="Ground Truth gate"):
        evaluate_benchmark([reference], [prediction])
    reference["annotation_status"] = "single_verified"
    prediction["item_id"] = "OTHER"
    with pytest.raises(ValueError, match="ID sets differ"):
        evaluate_benchmark([reference], [prediction])
