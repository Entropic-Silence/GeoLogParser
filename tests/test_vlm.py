import json
from pathlib import Path

import pytest

from geologparser.schema import validate_record
from geologparser.vlm import compact_payload_to_record, parse_json_object


def test_parse_json_object_accepts_fence_and_rejects_trailing_prose():
    assert parse_json_object('```json\n{"intervals": []}\n```') == {"intervals": []}
    with pytest.raises(ValueError):
        parse_json_object('{"intervals": []} this is extra')


def test_compact_vlm_payload_is_schema_valid_and_ungrounded():
    payload = {
        "borehole": {"borehole_id": "ZK7", "final_depth_m": "4.50"},
        "intervals": [{
            "top_depth_m": 0, "bottom_depth_m": "4.50", "thickness_m": "bad",
            "lithology_raw": "粉质黏土",
        }],
    }
    record = compact_payload_to_record(
        payload, document_id="D1", source_file=Path("page.png"), source_sha256="a" * 64,
    )
    validate_record(record)
    assert record["borehole"]["final_depth_m"]["value"] == 4.5
    assert record["intervals"][0]["thickness_m"]["value"] is None
    assert record["intervals"][0]["lithology_raw"]["warning_codes"] == ["VLM_UNGROUNDED"]
    assert record["intervals"][0]["lithology_normalized"]["value"] is None


def test_parse_json_object_requires_object():
    with pytest.raises(ValueError):
        parse_json_object(json.dumps([]))


def test_compact_payload_supports_text_only_llm_provenance():
    record = compact_payload_to_record(
        {"borehole": {"borehole_id": "BH1"}, "intervals": []},
        document_id="D", source_file=Path("source.pdf"), extraction_method="llm",
    )
    assert record["borehole"]["borehole_id"]["extraction_method"] == "llm"
    assert record["borehole"]["borehole_id"]["warning_codes"] == ["LLM_UNGROUNDED"]
