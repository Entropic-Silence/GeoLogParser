from geologparser.layout import extract_depth_column_intervals
from geologparser.ocr import TextRegion
from geologparser.schema import validate_record
from geologparser.io.records import empty_borehole_record


def test_layout_extracts_dominant_depth_column_and_description():
    regions = [
        TextRegion(1, (108, 140, 135, 150), "0.00 - 1.00", None, "direct_pdf_text"),
        TextRegion(1, (145, 118, 350, 136), "Brown moist silty sand.", None, "direct_pdf_text"),
        TextRegion(1, (108, 240, 135, 250), "1.00 - 2.50", None, "direct_pdf_text"),
        TextRegion(1, (145, 210, 350, 230), "Gray fine sand.", None, "direct_pdf_text"),
        TextRegion(1, (108, 340, 135, 350), "2.50 - 4.00", None, "direct_pdf_text"),
        TextRegion(1, (145, 310, 350, 330), "Stiff clay.", None, "direct_pdf_text"),
        TextRegion(1, (406, 250, 430, 260), "2.50 - 3.00", None, "direct_pdf_text"),
    ]
    intervals = extract_depth_column_intervals(regions)
    assert [(item["top_depth_m"]["value"], item["bottom_depth_m"]["value"]) for item in intervals] == [
        (0.0, 1.0), (1.0, 2.5), (2.5, 4.0),
    ]
    assert intervals[1]["description_raw"]["value"] == "Gray fine sand."
    record = empty_borehole_record("D1", "page.pdf")
    record["intervals"] = intervals
    validate_record(record)


def test_layout_abstains_on_isolated_prose_ranges():
    regions = [
        TextRegion(1, (280, 300, 600, 320), "Test from 8.50 m - 9.00 m", None, "direct_pdf_text"),
        TextRegion(1, (280, 330, 600, 350), "gravel to 9.40 m", None, "direct_pdf_text"),
    ]
    assert extract_depth_column_intervals(regions) == []
