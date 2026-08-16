from geologparser.layout import classify_borehole_page


def rows(*items):
    return [{"bbox": [10, 10 + index * 20, 120, 25 + index * 20], "text": text, "confidence": 0.9} for index, text in enumerate(items)]


def test_page_family_routes_explicit_depth_range_table():
    assessment = classify_borehole_page(
        rows("Thickness", "Recovered", "Depth", "from", "Surface"),
        width=1000, height=1600,
    )
    assert assessment.family == "explicit_depth_range_table"


def test_page_family_routes_scaled_composite_log():
    assessment = classify_borehole_page(
        rows("Stratigraphy", "Graphic Log", "Depth Drilled below K.B."),
        width=1000, height=1600,
    )
    assert assessment.family == "scaled_composite_log"


def test_page_family_abstains_without_structural_semantics():
    assessment = classify_borehole_page(rows("Borehole", "Date", "Contractor"), width=1000, height=1600)
    assert assessment.family == "unsupported"
