"""Layout-aware positioned-text baseline components."""

from .columns import DepthRangeCandidate, extract_depth_column_intervals
from .depth_semantics import (
    DepthBoundaryCandidate, DepthScaleCalibration, LogisticCandidateRanker,
    NumericEvidence, aggregate_numeric_evidence, detect_graphic_log_column,
    detect_graphic_log_columns, fit_depth_scale, graphic_boundary_candidates,
    multicolumn_graphic_boundary_candidates, printed_boundary_candidates,
    metadata_final_depth_candidates,
)
from .long_page import (
    LogPanelLayout, PageTile, SemanticAnchor, infer_log_panel_layout,
    long_page_tiles, semantic_anchors, tile_bbox_to_page,
)

__all__ = [
    "DepthBoundaryCandidate", "DepthRangeCandidate", "DepthScaleCalibration",
    "LogPanelLayout", "LogisticCandidateRanker", "NumericEvidence", "PageTile",
    "SemanticAnchor", "aggregate_numeric_evidence", "detect_graphic_log_column",
    "detect_graphic_log_columns", "multicolumn_graphic_boundary_candidates",
    "extract_depth_column_intervals", "infer_log_panel_layout", "long_page_tiles",
    "fit_depth_scale", "graphic_boundary_candidates", "printed_boundary_candidates",
    "metadata_final_depth_candidates", "semantic_anchors", "tile_bbox_to_page",
]
