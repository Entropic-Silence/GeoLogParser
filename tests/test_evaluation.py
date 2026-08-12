import pytest

from geologparser.evaluation import (
    boundary_accuracy,
    brier_score,
    exact_match,
    expected_calibration_error,
    interval_prf1,
    mean_absolute_error,
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

