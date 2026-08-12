import pytest

from geologparser.confidence import ConfidenceComponents, TemperatureScaler, fuse_confidence
from geologparser.evaluation import brier_score, expected_calibration_error


def test_confidence_fusion_renormalizes_only_available_components():
    fused = fuse_confidence(ConfidenceComponents(extraction=0.8, ocr=0.6))
    assert fused.value == pytest.approx((0.8 * 0.25 + 0.6 * 0.20) / 0.45)
    assert sum(fused.weights_used.values()) == pytest.approx(1)


def test_confidence_fusion_with_no_evidence_is_unknown():
    assert fuse_confidence(ConfidenceComponents()).value is None


def test_confidence_fusion_rejects_bad_inputs():
    with pytest.raises(ValueError):
        fuse_confidence(ConfidenceComponents(ocr=1.2))
    with pytest.raises(ValueError):
        fuse_confidence(ConfidenceComponents(ocr=0.8), {"invented": 1})


def test_temperature_scaler_identity_and_bounds():
    scaler = TemperatureScaler(1.0)
    assert scaler.transform([0.2, 0.8]) == pytest.approx([0.2, 0.8])
    assert 0 < scaler.transform_one(0) < 0.001
    assert 0.999 < scaler.transform_one(1) < 1


def test_temperature_fit_improves_overconfident_fixture_metrics():
    labels = [1, 0, 1, 0]
    probabilities = [0.99, 0.99, 0.95, 0.95]
    scaler = TemperatureScaler.fit(labels, probabilities)
    calibrated = scaler.transform(probabilities)
    assert scaler.temperature > 1
    assert brier_score(labels, calibrated).value < brier_score(labels, probabilities).value
    assert expected_calibration_error(labels, calibrated, bins=2).value < expected_calibration_error(labels, probabilities, bins=2).value


def test_temperature_fit_rejects_empty_observations():
    with pytest.raises(ValueError):
        TemperatureScaler.fit([], [])
