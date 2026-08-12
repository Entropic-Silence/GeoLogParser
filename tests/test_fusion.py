from pathlib import Path

from geologparser.extraction.fusion import fuse_records
from geologparser.io.records import empty_borehole_record, empty_interval, field


def records():
    grounded = empty_borehole_record("D1", str(Path("source.pdf")))
    visual = empty_borehole_record("D1", str(Path("page.png")), "image")
    return grounded, visual


def test_fusion_agreement_keeps_grounded_bbox_and_records_agreement():
    grounded, visual = records()
    grounded["borehole"]["borehole_id"] = field(
        "ZK1", source_page=1, source_bbox=[1, 2, 3, 4], extraction_method="direct_pdf_text",
    )
    visual["borehole"]["borehole_id"] = field("ZK1", extraction_method="vlm", confidence=0.8)
    fused, decisions = fuse_records(grounded, visual)
    assert fused["borehole"]["borehole_id"]["source_bbox"] == [1, 2, 3, 4]
    assert fused["borehole"]["borehole_id"]["extraction_method"] == "fusion"
    assert any(item["decision"] == "agreement_keep_grounded_provenance" for item in decisions)


def test_fusion_disagreement_never_silently_overwrites_grounded_value():
    grounded, visual = records()
    grounded["borehole"]["final_depth_m"] = field(4.5, extraction_method="ocr")
    visual["borehole"]["final_depth_m"] = field(45.0, extraction_method="vlm")
    fused, decisions = fuse_records(grounded, visual)
    field_value = fused["borehole"]["final_depth_m"]
    assert field_value["value"] == 4.5
    assert field_value["validation_status"] == "needs_review"
    assert "FUSION_DISAGREEMENT" in field_value["warning_codes"]
    assert any(item.get("visual_value") == 45.0 for item in decisions)


def test_visual_only_intervals_are_retained_but_not_auto_accepted():
    grounded, visual = records()
    interval = empty_interval("I001")
    interval["bottom_depth_m"] = field(3.2, extraction_method="vlm")
    visual["intervals"] = [interval]
    fused, decisions = fuse_records(grounded, visual)
    assert fused["intervals"][0]["bottom_depth_m"]["value"] == 3.2
    assert fused["intervals"][0]["bottom_depth_m"]["validation_status"] == "needs_review"
    assert "FUSION_UNALIGNED_VISUAL_INTERVAL" in fused["intervals"][0]["bottom_depth_m"]["warning_codes"]
    assert decisions[-1]["decision"] == "visual_intervals_unaligned_needs_review"
