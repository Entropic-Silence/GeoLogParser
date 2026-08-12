import copy
import json
from pathlib import Path

import pytest

from geologparser.spatial import attach_source_location, merge_verified_page_annotations


ROOT = Path(__file__).resolve().parents[1]


def record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def annotation(page, status="single_verified"):
    source = record()
    source["document"]["metadata"]["source_record_id"] = "PS1"
    source["document"]["document_id"] = f"UNIPD_PS1_P{page:03d}"
    for interval in source["intervals"]:
        for name, envelope in interval.items():
            if name != "interval_id":
                envelope["source_page"] = page
    return {
        "annotation_id": source["document"]["document_id"],
        "annotation_status": status,
        "panel": {"source_page": page},
        "record": source,
    }


def location():
    return {
        "longitude": 10.9, "latitude": 44.6, "coordinate_system": "EPSG:4326",
        "coordinate_source": "source_repository_kmz",
        "coordinate_validation_status": "source_provided_unverified",
        "link_key": "PS1", "warning_codes": [],
    }


def test_attach_source_location_preserves_unverified_status_and_provenance():
    source = record()
    linked = attach_source_location(source, location())
    assert source["borehole"]["x_coordinate"]["value"] is None
    assert linked["borehole"]["x_coordinate"]["value"] == 10.9
    assert linked["borehole"]["x_coordinate"]["validation_status"] == "needs_review"
    assert "SOURCE_COORDINATE_UNVERIFIED" in linked["borehole"]["x_coordinate"]["warning_codes"]
    assert linked["document"]["metadata"]["source_location_validation_status"] == "source_provided_unverified"


def test_attach_source_location_rejects_coordinate_conflict():
    source = record()
    source["borehole"]["x_coordinate"]["value"] = 1.0
    with pytest.raises(ValueError, match="conflicting x_coordinate"):
        attach_source_location(source, location())


def test_merge_verified_pages_renumbers_intervals_and_rejects_auto():
    merged = merge_verified_page_annotations([annotation(2), annotation(1)])
    assert merged["document"]["document_id"] == "UNIPD_PS1"
    assert merged["document"]["page_count"] == 2
    assert [item["interval_id"] for item in merged["intervals"]] == ["I001", "I002", "I003", "I004"]
    assert merged["intervals"][0]["top_depth_m"]["source_page"] == 1
    with pytest.raises(ValueError, match="human-verified"):
        merge_verified_page_annotations([annotation(1, "auto")])


def test_merge_verified_pages_rejects_disagreeing_headers():
    first, second = annotation(1), annotation(2)
    second = copy.deepcopy(second)
    second["record"]["borehole"]["borehole_id"]["value"] = "OTHER"
    with pytest.raises(ValueError, match="conflicting human page values"):
        merge_verified_page_annotations([first, second])
