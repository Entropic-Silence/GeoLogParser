"""Model-independent evaluation contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class MetricResult:
    name: str
    value: float | None
    numerator: float
    denominator: float
    unit: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Metric(Protocol):
    name: str

    def compute(self, references: Sequence[Any], predictions: Sequence[Any]) -> MetricResult: ...


def validate_pairs(references: Sequence[Any], predictions: Sequence[Any]) -> None:
    if len(references) != len(predictions):
        raise ValueError(f"reference/prediction length mismatch: {len(references)} != {len(predictions)}")

