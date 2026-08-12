"""Composable constraint engine."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .base import ConstraintResult, GeologicalConstraint
from .depth import (
    ContinuityConstraint,
    DepthValidityConstraint,
    FinalDepthConsistencyConstraint,
    MonotonicityConstraint,
    ThicknessConsistencyConstraint,
)
from .semantic import (
    CoordinateFormatConstraint,
    FieldTypeConsistencyConstraint,
    GroundwaterReasonablenessConstraint,
    PercentageRangeConstraint,
    StratumCodeSequenceConstraint,
)


class ConstraintEngine:
    def __init__(self, constraints: Iterable[GeologicalConstraint]) -> None:
        self.constraints = tuple(constraints)

    def evaluate(self, record: Mapping[str, Any]) -> tuple[ConstraintResult, ...]:
        return tuple(constraint.evaluate(record) for constraint in self.constraints)


def default_engine(tolerance_m: str = "0.05") -> ConstraintEngine:
    return ConstraintEngine((
        DepthValidityConstraint(),
        ThicknessConsistencyConstraint(tolerance_m),
        ContinuityConstraint(tolerance_m),
        MonotonicityConstraint(),
        FinalDepthConsistencyConstraint(tolerance_m),
        GroundwaterReasonablenessConstraint(),
        PercentageRangeConstraint(),
        CoordinateFormatConstraint(),
        StratumCodeSequenceConstraint(),
        FieldTypeConsistencyConstraint(),
    ))
