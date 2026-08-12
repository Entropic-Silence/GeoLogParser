"""Generate small, clearly synthetic schema fixtures (never benchmark data)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from geologparser.io import empty_borehole_record, empty_interval, field


ROOT = Path(__file__).resolve().parents[1]


def human(value, text=None, unit=None):
    return field(
        value,
        source_page=1,
        source_bbox=None,
        source_text=str(value) if text is None and value is not None else text,
        extraction_method="human",
        confidence=1.0 if value is not None else None,
        validation_status="human_verified" if value is not None else "not_validated",
        raw_unit=unit,
    )


def make_interval(identifier, top, bottom, thickness, raw_lithology, normalized_lithology, description):
    item = empty_interval(identifier)
    item["top_depth_m"] = human(top, f"{top:.2f}", "m")
    item["bottom_depth_m"] = human(bottom, f"{bottom:.2f}", "m")
    item["thickness_m"] = human(thickness, f"{thickness:.2f}", "m")
    item["lithology_raw"] = human(raw_lithology)
    item["lithology_normalized"] = human(normalized_lithology)
    item["description_raw"] = human(description)
    item["description_normalized"] = human(description)
    return item


def base_record(identifier, final_depth):
    record = empty_borehole_record(f"synthetic-{identifier}", f"synthetic/{identifier}.png", "image")
    record["document"]["metadata"].update({
        "template_id": "SYNTH-T01", "project_id": "SYNTH-P01", "source_id": "SYNTH",
        "quality": "high", "contains_stamp": False, "contains_handwriting": False, "dpi": 300,
    })
    record["borehole"]["borehole_id"] = human(identifier)
    record["borehole"]["project_name"] = human("仅用于测试的合成项目")
    record["borehole"]["page_id"] = human("1")
    record["borehole"]["collar_elevation_m"] = human(42.6, "42.60", "m")
    record["borehole"]["final_depth_m"] = human(final_depth, f"{final_depth:.2f}", "m")
    return record


def examples():
    valid = base_record("SYN-ZK01", 4.5)
    valid["borehole"]["groundwater_depth_m"] = human(2.1, "2.10", "m")
    valid["intervals"] = [
        make_interval("I001", 0.0, 1.2, 1.2, "杂填土", "杂填土", "灰褐色，松散"),
        make_interval("I002", 1.2, 4.5, 3.3, "亚粘土", "粉质黏土", "黄褐色，可塑"),
    ]

    missing = base_record("SYN-ZK02", 3.0)
    missing["borehole"]["collar_elevation_m"] = field()
    missing["intervals"] = [make_interval("I001", 0.0, 3.0, 3.0, "粉砂", "粉砂", "描述栏缺失")]
    missing["intervals"][0]["description_raw"] = field()
    missing["intervals"][0]["description_normalized"] = field()

    gap = base_record("SYN-ZK03", 5.0)
    gap["intervals"] = [
        make_interval("I001", 0.0, 2.0, 2.0, "黏土", "黏土", "可塑"),
        make_interval("I002", 2.2, 5.0, 2.8, "粉砂", "粉砂", "稍密"),
    ]

    mismatch = base_record("SYN-ZK04", 5.0)
    mismatch["intervals"] = [make_interval("I001", 0.0, 4.5, 4.2, "泥岩", "泥岩", "强风化")]

    low_confidence = deepcopy(valid)
    low_confidence["document"]["document_id"] = "synthetic-SYN-ZK05"
    low_confidence["document"]["source_file"] = "synthetic/SYN-ZK05.png"
    low_confidence["document"]["metadata"]["quality"] = "low"
    low_confidence["borehole"]["borehole_id"] = human("SYN-ZK05")
    low_confidence["intervals"][1]["bottom_depth_m"].update({
        "source_text": "4.?0", "extraction_method": "ocr", "confidence": 0.41,
        "validation_status": "needs_review", "warning_codes": ["OCR_DIGIT_UNCERTAIN"],
    })
    return {
        "synthetic_valid.json": valid,
        "synthetic_missing_fields.json": missing,
        "synthetic_continuity_gap.json": gap,
        "synthetic_thickness_final_mismatch.json": mismatch,
        "synthetic_low_confidence.json": low_confidence,
    }


def main():
    destination = ROOT / "examples" / "boreholes"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, record in examples().items():
        (destination / filename).write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()

