from geologparser.layout.column_roles import (
    assign_column_roles,
    infer_column_role_anchors,
    select_graphical_roles,
)


def test_composite_headers_anchor_graphic_log_and_depth_drilled():
    rows = [
        {"bbox": [100, 200, 260, 230], "text": "Stratigraphy", "confidence": 0.95},
        {"bbox": [300, 195, 350, 225], "text": "Depth", "confidence": 0.9},
        {"bbox": [355, 195, 430, 225], "text": "Drilled", "confidence": 0.9},
        {"bbox": [450, 195, 520, 225], "text": "Graphic", "confidence": 0.95},
        {"bbox": [525, 195, 560, 225], "text": "Log", "confidence": 0.95},
        {"bbox": [600, 195, 660, 225], "text": "Core", "confidence": 0.95},
    ]
    anchors = infer_column_role_anchors(rows, width=1000, height=1000, header_y=0.21)
    by_role = {anchor.role: anchor for anchor in anchors}
    assert by_role["graphic_log"].center_x > 0.45
    assert by_role["depth_drilled"].center_x < by_role["graphic_log"].center_x


def test_role_gate_rejects_texture_bearing_stratigraphy_and_keeps_graphic():
    rows = [
        {"bbox": [100, 200, 260, 230], "text": "Stratigraphy", "confidence": 0.95},
        {"bbox": [300, 195, 350, 225], "text": "Depth", "confidence": 0.9},
        {"bbox": [355, 195, 430, 225], "text": "Drilled", "confidence": 0.9},
        {"bbox": [450, 195, 520, 225], "text": "Graphic", "confidence": 0.95},
        {"bbox": [525, 195, 560, 225], "text": "Log", "confidence": 0.95},
        {"bbox": [600, 195, 660, 225], "text": "Core", "confidence": 0.95},
    ]
    anchors = infer_column_role_anchors(rows, width=1000, height=1000, header_y=0.21)
    assignments = assign_column_roles(
        [(100, 260, 0.8), (300, 430, 0.8), (450, 560, 0.8), (600, 660, 0.8)],
        anchors, width=1000,
    )
    selected = select_graphical_roles(assignments)
    assert [item.role for item in selected] == ["graphic_log", "core"]
    assert all(item.role not in {"stratigraphy", "depth_drilled"} for item in selected)
