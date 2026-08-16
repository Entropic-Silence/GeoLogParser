"""Layout-aware positioned-text baseline components."""

from .columns import DepthRangeCandidate, extract_depth_column_intervals
from .depth_semantics import (
    DepthBoundaryCandidate, DepthScaleCalibration, LogisticCandidateRanker,
    NumericEvidence, aggregate_numeric_evidence, detect_graphic_log_column,
    detect_graphic_log_columns, fit_depth_scale, graphic_boundary_candidates,
    multicolumn_graphic_boundary_candidates, printed_boundary_candidates,
    role_aware_multicolumn_graphic_boundary_candidates, metadata_final_depth_candidates,
)
from .long_page import (
    LogPanelLayout, PageTile, SemanticAnchor, infer_log_panel_layout,
    long_page_tiles, semantic_anchors, tile_bbox_to_page,
)
from .page_family import (
    ExplicitDepthRange, PageFamilyAssessment, boundaries_from_ranges,
    classify_borehole_page, extract_explicit_depth_ranges,
    locate_explicit_depth_column,
)
from .native_pdf_structure import (
    NativeNumericColumn, NativePDFWord, NativeStructuralPrediction,
    extract_native_pdf_words, locate_named_log_pages, parse_native_number,
    predict_native_pdf_boundaries,
)

__all__ = [
    "DepthBoundaryCandidate", "DepthRangeCandidate", "DepthScaleCalibration",
    "LogPanelLayout", "LogisticCandidateRanker", "NumericEvidence", "PageTile",
    "SemanticAnchor", "ExplicitDepthRange", "PageFamilyAssessment",
    "NativeNumericColumn", "NativePDFWord", "NativeStructuralPrediction",
    "aggregate_numeric_evidence", "boundaries_from_ranges",
    "classify_borehole_page", "detect_graphic_log_column",
    "detect_graphic_log_columns", "multicolumn_graphic_boundary_candidates",
    "role_aware_multicolumn_graphic_boundary_candidates",
    "extract_depth_column_intervals", "infer_log_panel_layout", "long_page_tiles",
    "fit_depth_scale", "graphic_boundary_candidates", "printed_boundary_candidates",
    "extract_explicit_depth_ranges", "locate_explicit_depth_column",
    "metadata_final_depth_candidates", "semantic_anchors", "tile_bbox_to_page",
    "extract_native_pdf_words", "parse_native_number", "predict_native_pdf_boundaries",
    "locate_named_log_pages",
]
