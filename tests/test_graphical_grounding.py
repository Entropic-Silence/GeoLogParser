from __future__ import annotations

import cv2
import numpy as np

from geologparser.layout import (
    detect_graphical_boundary_events, fit_reference_blind_depth_axis,
)
from geologparser.layout.long_page import LogPanelLayout, SemanticAnchor


def _layout() -> LogPanelLayout:
    return LogPanelLayout(
        header_y=0.10, anchor_row_score=1,
        anchors={"description": SemanticAnchor("description", "DESCRIPTION", 1.0, 0.55, 0.12, (50, 10, 60, 20))},
        x_min=0.1, x_max=0.95, y_min=0.03, y_max=0.95,
    )


def test_reference_blind_axis_rejects_stray_metadata() -> None:
    rows = [
        {"text": "0.00", "bbox": [40, 20, 50, 30]},
        {"text": "10.00", "bbox": [40, 120, 50, 130]},
        {"text": "20.00", "bbox": [40, 220, 50, 230]},
        {"text": "30.00", "bbox": [40, 320, 50, 330]},
        {"text": "62.00", "bbox": [180, 30, 200, 40]},
    ]
    axis = fit_reference_blind_depth_axis(rows, width=300, height=400, layout=_layout())
    assert axis is not None
    assert axis.inlier_count == 4
    assert axis.rmse_m < 1e-6
    assert abs(axis.depth_at(225) - 20.0) < 0.1


def test_graphical_events_map_horizontal_contacts_to_depth() -> None:
    image = np.full((400, 300), 255, np.uint8)
    for y in (20, 120, 220, 320):
        cv2.line(image, (40, y), (230, y), 0, 2)
    rows = [
        {"text": "0.00", "bbox": [40, 15, 50, 25]},
        {"text": "10.00", "bbox": [40, 115, 50, 125]},
        {"text": "20.00", "bbox": [40, 215, 50, 225]},
        {"text": "30.00", "bbox": [40, 315, 50, 325]},
    ]
    axis = fit_reference_blind_depth_axis(rows, width=300, height=400, layout=_layout())
    assert axis is not None
    events = detect_graphical_boundary_events(image, layout=_layout(), axis=axis, description_x_center=0.55)
    depths = [round(event.depth_m) for event in events]
    assert {0, 10, 20, 30}.issubset(depths)
    assert all(event.confidence > 0 for event in events)
