from pathlib import Path

import pytest

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


def test_bgs_reference_and_grid_header_are_extracted_without_metadata_injection(tmp_path):
    source = tmp_path / "bgs.pdf"
    source.write_bytes(b"%PDF-fixture")
    region = TextRegion(
        page=1, bbox=(0, 0, 500, 100), confidence=0.88, method="ocr",
        text="BGS ID: 10 : BGS Reference: SD20NE9\nBritish National Grid (27700) : 328244, 408488",
    )
    result = extract_structured([region], source)
    assert result["borehole"]["borehole_id"]["value"] == "SD20NE9"
    assert result["borehole"]["coordinate_system"]["value"] == "EPSG:27700"
    assert result["borehole"]["x_coordinate"]["value"] == 328244
    assert result["borehole"]["y_coordinate"]["value"] == 408488
    assert result["borehole"]["final_depth_m"]["value"] is None


def test_bgs_grid_header_tolerates_ocr_deleted_spaces(tmp_path):
    source = tmp_path / "bgs.pdf"
    source.write_bytes(b"%PDF-fixture")
    region = TextRegion(
        page=1, bbox=(10, 20, 300, 60), confidence=0.97, method="ocr",
        text="BritishNationalGrid (27700) :329168,405889",
    )
    result = extract_structured([region], source)
    assert result["borehole"]["coordinate_system"]["value"] == "EPSG:27700"
    assert result["borehole"]["x_coordinate"]["value"] == 329168
    assert result["borehole"]["y_coordinate"]["value"] == 405889
    assert result["borehole"]["x_coordinate"]["source_bbox"] == [10, 20, 300, 60]


def test_international_headers_support_plain_borehole_and_decimal_comma(tmp_path):
    source = tmp_path / "italian.pdf"
    source.write_bytes(b"%PDF-fixture")
    region = TextRegion(
        page=1, bbox=(0, 0, 500, 100), confidence=None, method="direct_pdf_text",
        text="Borehole: P S1\nElevation: 35,22 m above sea level\nWater table: -5,80 m",
    )
    result = extract_structured([region], source)
    assert result["borehole"]["borehole_id"]["value"] == "PS1"
    assert result["borehole"]["collar_elevation_m"]["value"] == 35.22
    assert result["borehole"]["groundwater_depth_m"]["value"] == -5.8
    compact = TextRegion(1, None, "BOREHOLE: TPS7 CLIENT: Example", None, "direct_pdf_text")
    assert extract_structured([compact], source)["borehole"]["borehole_id"]["value"] == "TPS7"


def test_native_multiline_chinese_header_preserves_block_evidence(tmp_path):
    source = tmp_path / "chinese.pdf"
    source.write_bytes(b"%PDF-fixture")
    regions = [
        TextRegion(44, (10, 20, 300, 60), "工程名称\n项目甲\n工 程 编 号\nP01", None, "direct_pdf_text"),
        TextRegion(44, (10, 70, 180, 100), "孔    号\nZK2", None, "direct_pdf_text"),
        TextRegion(44, (190, 70, 360, 100), "X=2922958.785", None, "direct_pdf_text"),
        TextRegion(44, (190, 105, 360, 135), "Y=39578564.975", None, "direct_pdf_text"),
        TextRegion(44, (10, 105, 180, 135), "孔口标高\n127.14m", None, "direct_pdf_text"),
        TextRegion(44, (370, 70, 520, 100), "稳定水位深度7.95m", None, "direct_pdf_text"),
        TextRegion(44, (370, 105, 520, 135), "终孔深度\n21.30m", None, "direct_pdf_text"),
        TextRegion(44, (530, 105, 700, 135), "终 孔 日 期\n2023/6/4", None, "direct_pdf_text"),
    ]
    result = extract_structured(regions, source)
    assert result["borehole"]["project_name"]["value"] == "项目甲"
    assert result["borehole"]["borehole_id"]["value"] == "ZK2"
    assert result["borehole"]["x_coordinate"]["value"] == 2922958.785
    assert result["borehole"]["y_coordinate"]["value"] == 39578564.975
    assert result["borehole"]["collar_elevation_m"]["value"] == 127.14
    assert result["borehole"]["groundwater_depth_m"]["value"] == 7.95
    assert result["borehole"]["final_depth_m"]["value"] == 21.3
    assert result["borehole"]["drilling_date"]["value"] == "2023-06-04"
    assert result["borehole"]["borehole_id"]["source_bbox"] == [10, 70, 180, 100]


def test_native_stratum_row_derives_top_without_repurposing_elevation(tmp_path):
    source = tmp_path / "chinese.pdf"
    source.write_bytes(b"%PDF-fixture")
    region = TextRegion(
        44, (10, 200, 400, 240), "K\n④\n105.84\n21.30\n14.00", None, "direct_pdf_text",
    )
    result = extract_structured([region], source)
    interval = result["intervals"][0]
    assert interval["stratum_code_raw"]["value"] == "④"
    assert interval["top_depth_m"]["value"] == pytest.approx(7.3)
    assert interval["top_depth_m"]["extraction_method"] == "derived"
    assert interval["bottom_depth_m"]["value"] == 21.3
    assert interval["bottom_depth_m"]["source_text"] == "elevation=105.84; bottom=21.30"
    assert interval["thickness_m"]["value"] == 14.0


def test_native_stratum_row_can_precede_description_and_generic_footer_is_skipped(tmp_path):
    source = tmp_path / "chinese.pdf"
    source.write_bytes(b"%PDF-fixture")
    regions = [
        TextRegion(44, (1, 1, 10, 10), "工程名称\n图件名称", None, "direct_pdf_text"),
        TextRegion(44, (1, 20, 100, 40), "工程名称\n真实项目\n工程编号\nP01", None, "direct_pdf_text"),
        TextRegion(
            44, (1, 50, 300, 80),
            "K\n③\n113.57\n12.50\n1.20\nf\n碎块状强风化粉砂岩", None, "direct_pdf_text",
        ),
    ]
    result = extract_structured(regions, source)
    assert result["borehole"]["project_name"]["value"] == "真实项目"
    assert len(result["intervals"]) == 1
    assert result["intervals"][0]["stratum_code_raw"]["value"] == "③"
    assert result["intervals"][0]["top_depth_m"]["value"] == pytest.approx(11.3)


def test_native_description_binding_requires_equal_ordered_heading_count(tmp_path):
    source = tmp_path / "chinese.pdf"
    source.write_bytes(b"%PDF-fixture")
    regions = [
        TextRegion(1, (10, 100, 400, 140), "① 99.00 1.00 1.00 素填土:杂色，稍湿", None, "direct_pdf_text"),
        TextRegion(1, (20, 100, 400, 140), "以松散状为主，含少量碎石。", None, "direct_pdf_text"),
        TextRegion(1, (50, 100, 400, 140), "② 98.00 2.00 1.00", None, "direct_pdf_text"),
        TextRegion(1, (60, 100, 400, 140), "中风化粉砂岩:紫红色，层状构造", None, "direct_pdf_text"),
        TextRegion(1, (70, 100, 400, 140), "岩芯呈短柱状，裂隙较发育。", None, "direct_pdf_text"),
    ]
    result = extract_structured(regions, source)
    assert [item["lithology_raw"]["value"] for item in result["intervals"]] == ["素填土", "中风化粉砂岩"]
    assert "松散状" in result["intervals"][0]["description_raw"]["value"]
    assert "短柱状" in result["intervals"][1]["description_raw"]["value"]
    assert result["intervals"][0]["description_raw"]["source_bbox"] == [10, 100, 400, 140]

    unmatched = extract_structured(regions[:-2], source)
    assert len(unmatched["intervals"]) == 2
    assert all(item["lithology_raw"]["value"] is None for item in unmatched["intervals"])
