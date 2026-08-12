from pathlib import Path

from geologparser.extraction import extract_structured
from geologparser.ocr import TextRegion
from geologparser.schema import validate_record


def test_regex_extractor_is_conservative_and_preserves_evidence(tmp_path):
    source = tmp_path / "sample.png"
    source.write_bytes(b"fixture")
    region = TextRegion(
        page=1, bbox=(10, 20, 300, 60), confidence=0.91, method="ocr",
        text="孔号: ZK-01 终孔深度: 4.50m\n0.00 1.20 1.20 杂填土 松散\n1.20 4.50 3.30 粉质黏土 可塑",
    )
    result = extract_structured([region], source)
    assert result["borehole"]["borehole_id"]["value"] == "ZK-01"
    assert result["borehole"]["final_depth_m"]["value"] == 4.5
    assert len(result["intervals"]) == 2
    assert result["intervals"][1]["lithology_raw"]["value"] == "粉质黏土"
    assert result["intervals"][1]["lithology_normalized"]["value"] is None
    assert result["intervals"][0]["bottom_depth_m"]["source_bbox"] == [10, 20, 300, 60]
    assert result["borehole"]["groundwater_depth_m"]["value"] is None
    validate_record(result)
