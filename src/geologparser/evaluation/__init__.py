from .evaluator import Evaluator
from .benchmark import evaluate_benchmark
from .synthetic import evaluate_synthetic_controlled
from .correction import correction_safety_metrics, review_detection_metrics
from .paper2 import evaluate_paper2_ablation_matrix, evaluate_paper2_cases
from .errors import ERROR_TAXONOMY_V001, classify_field_error, error_distribution
from .error_propagation import (
    SurfacePoint, aggregate_repeated_metrics, boundary_surface_points, idw_predict, perturb_interval_boundaries,
    spatial_model_readiness, surface_error_metrics,
)
from .source_surface import (
    SourceFieldSurface, convex_hull_xy, load_coal_602_roof_depth_surface,
    perturb_surface_scalar, regular_queries_within_hull,
)
from .metrics import (
    IntervalMatch,
    boundary_matched_interval_metrics,
    boundary_accuracy,
    brier_score,
    critical_numerical_error_rate,
    constraint_consistency_summary,
    exact_match,
    extraction_coverage,
    expected_calibration_error,
    hierarchical_classification_metrics,
    interval_prf1,
    match_intervals_by_boundaries,
    mean_absolute_error,
    numeric_with_missing_mae,
    character_error_rate,
    numeric_character_error_rate,
    normalized_edit_similarity,
    sequence_error_rate,
    word_error_rate,
)
from .types import Metric, MetricResult

__all__ = [
    "Evaluator", "IntervalMatch", "Metric", "MetricResult", "SurfacePoint", "boundary_accuracy",
    "boundary_matched_interval_metrics", "brier_score", "constraint_consistency_summary",
    "critical_numerical_error_rate", "hierarchical_classification_metrics",
    "exact_match", "extraction_coverage", "expected_calibration_error", "interval_prf1",
    "match_intervals_by_boundaries", "mean_absolute_error", "numeric_with_missing_mae",
    "boundary_surface_points", "idw_predict", "perturb_interval_boundaries",
    "surface_error_metrics", "spatial_model_readiness", "aggregate_repeated_metrics", "ERROR_TAXONOMY_V001", "classify_field_error",
    "SourceFieldSurface", "convex_hull_xy", "load_coal_602_roof_depth_surface",
    "perturb_surface_scalar", "regular_queries_within_hull",
    "error_distribution", "character_error_rate", "numeric_character_error_rate",
    "normalized_edit_similarity",
    "sequence_error_rate", "word_error_rate",
    "correction_safety_metrics", "review_detection_metrics",
    "evaluate_benchmark", "evaluate_synthetic_controlled", "evaluate_paper2_ablation_matrix", "evaluate_paper2_cases",
]
