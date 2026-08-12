import pytest

from geologparser.evaluation import (
    boundary_accuracy,
    brier_score,
    exact_match,
    extraction_coverage,
    expected_calibration_error,
    interval_prf1,
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

