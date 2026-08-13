import json
from pathlib import Path

import pytest

from geologparser.schema import load_schema, validate_record


ROOT = Path(__file__).resolve().parents[1]


def test_schema_declares_v001_and_provenance():
    schema = load_schema()
    assert schema["properties"]["schema_version"]["const"] == "v001"
    assert "source_bbox" in schema["$defs"]["evidence"]["required"]
    assert "display_bbox" in schema["$defs"]["evidence"]["properties"]
    assert "display_bbox_source" in schema["$defs"]["evidence"]["properties"]
    assert "display_bbox_annotator_id" in schema["$defs"]["evidence"]["properties"]
    assert "raw_unit" in schema["$defs"]["evidence"]["properties"]


@pytest.mark.parametrize("path", sorted((ROOT / "examples" / "boreholes").glob("*.json")))
def test_all_synthetic_examples_validate(path):
    validate_record(json.loads(path.read_text(encoding="utf-8")))


def test_unknown_top_level_property_is_rejected():
    record = json.loads((ROOT / "examples" / "boreholes" / "synthetic_valid.json").read_text(encoding="utf-8"))
    record["invented"] = 1
    with pytest.raises(Exception):
        validate_record(record)
