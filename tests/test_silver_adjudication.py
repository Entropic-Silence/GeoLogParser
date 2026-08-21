import json
from pathlib import Path

import pytest

from geologparser.silver_adjudication import adjudicate_records, build_padova_silver


def _record():
    return json.loads(Path("examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def _set(record, field, value):
    record["borehole"][field]["value"] = value
    return record


def test_field_adjudication_withholds_unresolved_numeric_conflict():
    a = _set(_record(), "final_depth_m", 10.0)
    b = _set(_record(), "final_depth_m", 11.0)
    c = _record()
    row = adjudicate_records("X", a, b, c, source_metadata={"item_id": "X"}, run_metadata={"protocol": "test"})
    field = row["silver_label"]["borehole"]["final_depth_m"]
    decision = next(item for item in row["field_decisions"] if item["path"] == "borehole.final_depth_m")
    assert field["value"] is None
    assert decision["status"] == "DISAGREEMENT_UNRESOLVED"
    assert row["ground_truth_tier"] == "SILVER_UNCERTAIN"
    assert row["human_ground_truth"] is False


def test_field_adjudication_uses_layout_corroboration():
    a = _set(_record(), "final_depth_m", 10.0)
    b = _set(_record(), "final_depth_m", 11.0)
    c = _set(_record(), "final_depth_m", 10.0)
    row = adjudicate_records("X", a, b, c, source_metadata={"item_id": "X"}, run_metadata={"protocol": "test"})
    field = row["silver_label"]["borehole"]["final_depth_m"]
    decision = next(item for item in row["field_decisions"] if item["path"] == "borehole.final_depth_m")
    assert field["value"] == 10.0
    assert decision["status"] == "CORROBORATED_A"
    assert row["ground_truth_tier"] in {"SILVER_HIGH_CONFIDENCE", "SILVER_UNCERTAIN"}


def test_padova_builder_is_immutable(tmp_path: Path):
    root = tmp_path / "out"
    source = tmp_path / "source.jsonl"
    panel = tmp_path / "panel.jsonl"
    pred_a = tmp_path / "a.jsonl"
    pred_b = tmp_path / "b.jsonl"
    layout = tmp_path / "c.jsonl"
    record = _record()
    source.write_text("{}\n")
    panel.write_text(json.dumps({"panel_id": "X", "source_path": "x.pdf"}) + "\n")
    for path in (pred_a, pred_b, layout):
        path.write_text(json.dumps({"item_id": "X", "record": record}) + "\n")
    summary = build_padova_silver(root, source_manifest=source, panel_manifest=panel, extractor_a_path=pred_a, extractor_b_path=pred_b, layout_path=layout)
    assert summary["source_item_count"] == 1
    assert (root / "silver_reference.jsonl").is_file()
    assert (root / "artifact_manifest.json").is_file()
    with pytest.raises(FileExistsError):
        build_padova_silver(root, source_manifest=source, panel_manifest=panel, extractor_a_path=pred_a, extractor_b_path=pred_b, layout_path=layout)
