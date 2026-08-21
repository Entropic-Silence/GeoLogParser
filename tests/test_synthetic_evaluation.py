import copy
import json
from pathlib import Path

from geologparser.evaluation import evaluate_synthetic_controlled


def test_synthetic_evaluation_is_separate_from_human_gt():
    reference = json.loads(Path("examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    prediction = copy.deepcopy(reference)
    metrics = evaluate_synthetic_controlled([reference], [prediction])
    assert metrics["ground_truth_tier"] == "SYNTHETIC"
    assert metrics["formal_benchmark_eligible"] is False
    assert metrics["borehole_id_exact_match"]["value"] == 1.0


def test_synthetic_evaluation_requires_aligned_ids():
    reference = json.loads(Path("examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    prediction = copy.deepcopy(reference)
    prediction["document"]["document_id"] = "other"
    try:
        evaluate_synthetic_controlled([reference], [prediction])
    except ValueError as exc:
        assert "ID order" in str(exc)
    else:
        raise AssertionError("ID mismatch must fail")
