import pytest

from geologparser.evaluation import (
    boundary_accuracy,
    boundary_matched_interval_metrics,
    brier_score,
    exact_match,
    extraction_coverage,
    expected_calibration_error,
    interval_prf1,
    match_intervals_by_boundaries,
    mean_absolute_error,
    numeric_with_missing_mae,
)


def test_exact_and_numeric_metrics_keep_counts():
    exact = exact_match(["A", "B"], ["A", "C"])
    mae = mean_absolute_error([1.0, 3.0, None], [1.2, 2.6, 99.0])
    assert exact.value == 0.5
    assert exact.numerator == 1
    assert mae.value == pytest.approx(0.3)
    assert mae.denominator == 2


def test_boundary_accuracy_is_inclusive():
    result = boundary_accuracy([1.0, 2.0], [1.05, 2.051], tolerance=0.05)
    assert result.value == 0.5


def test_calibration_metrics():
    assert brier_score([1, 0], [0.8, 0.2]).value == pytest.approx(0.04)
    ece = expected_calibration_error([1, 0], [0.8, 0.2], bins=2)
    assert ece.value == pytest.approx(0.2)
    assert len(ece.details["bin_stats"]) == 2


def test_interval_prf1_exact_id_contract():
    results = interval_prf1([{"I1", "I2"}], [{"I2", "I3"}])
    assert results["interval_precision"].value == 0.5
    assert results["interval_recall"].value == 0.5
    assert results["interval_f1"].value == 0.5


def test_metric_length_mismatch_is_rejected():
    with pytest.raises(ValueError):
        exact_match([1], [1, 2])


def test_missing_numeric_predictions_require_coverage_reporting():
    results = numeric_with_missing_mae([10.0, 20.0], [11.0, None], "depth_mae")
    assert results["depth_mae"].value == 1.0
    assert results["depth_mae"].denominator == 1
    assert results["depth_mae_coverage"].value == 0.5
    assert extraction_coverage([None, "", 4.5]).value == pytest.approx(1 / 3)


def interval(top, bottom):
    return {"top_depth_m": {"value": top}, "bottom_depth_m": {"value": bottom}}


def test_boundary_matcher_is_inclusive_and_reports_unmatched():
    references = [interval(0, 1), interval(1, 2), interval(2, 3)]
    predictions = [interval(0.05, 1.05), interval(1, 2), interval(9, 10)]
    matches, unmatched_references, unmatched_predictions = match_intervals_by_boundaries(
        references, predictions, tolerance_m=0.05,
    )
    assert [(match.reference_index, match.prediction_index) for match in matches] == [(0, 0), (1, 1)]
    assert unmatched_references == [2]
    assert unmatched_predictions == [2]


def test_boundary_matcher_maximizes_count_then_minimizes_error():
    references = [interval(0, 1), interval(0.1, 1.1)]
    predictions = [interval(0.09, 1.09)]
    matches, _, _ = match_intervals_by_boundaries(references, predictions, tolerance_m=0.2)
    assert len(matches) == 1
    assert matches[0].reference_index == 1


def test_boundary_matcher_does_not_cross_depth_order():
    references = [interval(0, 1), interval(1, 2)]
    predictions = [interval(1, 2), interval(0, 1)]
    matches, _, _ = match_intervals_by_boundaries(references, predictions, tolerance_m=0)
    assert len(matches) == 1


def test_boundary_matched_metrics_keep_empty_denominators_null():
    empty = boundary_matched_interval_metrics([[]], [[]])
    assert empty["interval_precision"].value is None
    assert empty["interval_recall"].value is None
    assert empty["matched_top_boundary_mae_m"].value is None


def test_boundary_matched_metrics_are_micro_and_trace_counts():
    results = boundary_matched_interval_metrics(
        [[interval(0, 1), interval(1, 2)]],
        [[interval(0.01, 1.02), interval(8, 9)]],
        tolerance_m=0.05,
    )
    assert results["interval_precision"].value == 0.5
    assert results["interval_recall"].value == 0.5
    assert results["interval_f1"].value == 0.5
    assert results["matched_top_boundary_mae_m"].value == pytest.approx(0.01)
    assert results["matched_bottom_boundary_mae_m"].value == pytest.approx(0.02)
    assert results["interval_f1"].details["unmatched_reference_count"] == 1


def test_boundary_matcher_rejects_negative_tolerance_and_missing_boundaries():
    with pytest.raises(ValueError):
        match_intervals_by_boundaries([], [], tolerance_m=-0.01)
    matches, unmatched_references, unmatched_predictions = match_intervals_by_boundaries(
        [interval(None, 1)], [interval(0, 1)], tolerance_m=0.05,
    )
    assert matches == []
    assert unmatched_references == [0]
    assert unmatched_predictions == [0]
