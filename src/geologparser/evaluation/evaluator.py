from __future__ import annotations

from typing import Any, Mapping, Sequence

from .types import Metric, MetricResult


class Evaluator:
    def __init__(self, metrics: Sequence[Metric]) -> None:
        self.metrics = tuple(metrics)

    def evaluate(self, references: Sequence[Any], predictions: Sequence[Any]) -> Mapping[str, MetricResult]:
        return {metric.name: metric.compute(references, predictions) for metric in self.metrics}

