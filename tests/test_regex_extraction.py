from pathlib import Path

from geologparser.extraction import extract_structured
from geologparser.ocr.base import TextRegion


def test_borehole_log_title_is_not_misread_and_explicit_id_is_extracted():
    regions = [TextRegion(1, None, "BOREHOLE LOG\nID: SYN-0001", 1.0, "ocr")]
    record = extract_structured(regions, Path("source.png"))
    assert record["borehole"]["borehole_id"]["value"] == "SYN-0001"


def test_explicit_english_borehole_id_is_extracted():
    regions = [TextRegion(1, None, "BOREHOLE LOG\nBorehole ID: SYN-0001", 1.0, "ocr")]
    record = extract_structured(regions, Path("source.png"))
    assert record["borehole"]["borehole_id"]["value"] == "SYN-0001"
