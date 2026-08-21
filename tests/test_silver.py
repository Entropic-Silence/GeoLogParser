import copy
import json
from pathlib import Path

import pytest

from geologparser.silver import build_silver_dataset, run_silver_case


def _record(item_id: str, value: str):
    record = json.loads(Path("examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))
    record["document"]["document_id"] = item_id
    record["borehole"]["borehole_id"]["value"] = value
    return record


def test_extractors_are_independent_and_agreement_is_silver():
    seen = []

    def extractor_a(source):
        seen.append(("A", "prediction_b" in source))
        return {"extractor_id": "A", "record": _record(source["item_id"], "A")}

    def extractor_b(source):
        seen.append(("B", "prediction_a" in source))
        return {"extractor_id": "B", "record": _record(source["item_id"], "A")}

    result = run_silver_case({"item_id": "X", "image_path": "x.png"}, extractor_a, extractor_b)
    assert result["ground_truth_tier"] == "SILVER_HIGH_CONFIDENCE"
    assert result["human_ground_truth"] is False
    assert seen == [("A", False), ("B", False)]


def test_disagreement_becomes_hard_case():
    def extractor(value):
        return {"record": _record("X", value), "extractor_id": value}
    result = run_silver_case({"item_id": "X"}, lambda s: extractor("A"), lambda s: extractor("B"))
    assert result["agreement_status"] == "DISAGREEMENT"
    assert result["ground_truth_tier"] == "SILVER_UNCERTAIN"
    assert result["hard_case"] is True
    assert result["silver_label"] is None


def test_silver_output_is_immutable(tmp_path: Path):
    source = [{"item_id": "X"}]
    output = tmp_path / "silver"
    fn = lambda source: {"record": _record("X", "A")}
    summary = build_silver_dataset(source, output, fn, fn)
    assert summary["high_confidence_count"] == 1
    with pytest.raises(FileExistsError):
        build_silver_dataset(source, output, fn, fn)
