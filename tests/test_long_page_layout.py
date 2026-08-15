from geologparser.layout import infer_log_panel_layout
from geologparser.ocr import TextRegion


def test_semantic_layout_accepts_plural_descriptions_header():
    regions = [TextRegion(1, (420, 700, 650, 740), "DESCRIPTIONS", 0.98, "test")]
    layout = infer_log_panel_layout(regions, 1000, 2000)
    assert layout is not None
    assert layout.anchors["description"].text == "DESCRIPTIONS"
