"""Transparent confidence fusion and calibration primitives."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, log
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ConfidenceComponents:
    extraction: float | None = None
    cross_model_agreement: float | None = None
    constraint_consistency: float | None = None
    ocr: float | None = None
    layout: float | None = None


@dataclass(frozen=True)
class FusedConfidence:
    value: float | None
    components: ConfidenceComponents
    weights_used: Mapping[str, float]


def fuse_confidence(
    components: ConfidenceComponents,
    weights: Mapping[str, float] | None = None,
) -> FusedConfidence:
    weights = weights or {
        "extraction": 0.25, "cross_model_agreement": 0.20,
        "constraint_consistency": 0.25, "ocr": 0.20, "layout": 0.10,
    }
    values = asdict(components)
    unknown = set(weights) - set(values)
    if unknown:
        raise ValueError(f"unknown confidence components: {', '.join(sorted(unknown))}")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("confidence weights must be non-negative")
    available = {name: value for name, value in values.items() if value is not None and name in weights}
    if any(value < 0 or value > 1 for value in available.values()):
        raise ValueError("confidence components must be within [0, 1]")
    total_weight = sum(weights[name] for name in available)
    if total_weight == 0:
        return FusedConfidence(None, components, {})
    normalized_weights = {name: weights[name] / total_weight for name in available}
    fused = sum(available[name] * normalized_weights[name] for name in available)
    return FusedConfidence(fused, components, normalized_weights)


@dataclass(frozen=True)
class TemperatureScaler:
    temperature: float = 1.0
    epsilon: float = 1e-6

    def transform_one(self, probability: float) -> float:
        if probability < 0 or probability > 1:
            raise ValueError("probability must be within [0, 1]")
        clipped = min(1 - self.epsilon, max(self.epsilon, probability))
        logit = log(clipped / (1 - clipped)) / self.temperature
        return 1 / (1 + exp(-logit))

    def transform(self, probabilities: Sequence[float]) -> list[float]:
        return [self.transform_one(probability) for probability in probabilities]

    @classmethod
    def fit(
        cls,
        labels: Sequence[int],
        probabilities: Sequence[float],
        candidates: Sequence[float] | None = None,
    ) -> "TemperatureScaler":
        if len(labels) != len(probabilities):
            raise ValueError("label/probability length mismatch")
        if not labels:
            raise ValueError("temperature fitting requires observations")
        if any(label not in (0, 1) for label in labels):
            raise ValueError("labels must be binary")
        candidates = candidates or tuple(value / 20 for value in range(1, 201))
        if any(candidate <= 0 for candidate in candidates):
            raise ValueError("temperature candidates must be positive")

        def loss(temperature: float) -> float:
            scaler = cls(temperature)
            calibrated = scaler.transform(probabilities)
            epsilon = scaler.epsilon
            return -sum(
                label * log(max(epsilon, probability))
                + (1 - label) * log(max(epsilon, 1 - probability))
                for label, probability in zip(labels, calibrated)
            ) / len(labels)

        return cls(min(candidates, key=loss))
