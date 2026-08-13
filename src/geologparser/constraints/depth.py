"""Initial depth/topology constraints C1–C5."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from .base import (
    ConstraintViolation,
    GeologicalConstraint,
    as_decimal,
    intervals,
    make_result,
)


class DepthValidityConstraint(GeologicalConstraint):
    name = "C1_depth_validity"

    def __init__(self, severity: str = "error") -> None:
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index, item in enumerate(intervals(record)):
            top = as_decimal(item.get("top_depth_m"))
            bottom = as_decimal(item.get("bottom_depth_m"))
            if top is None or bottom is None:
                continue
            evaluated += 1
            if bottom <= top:
                prefix = f"intervals[{index}]"
                violations.append(ConstraintViolation(
                    code="DEPTH_NOT_INCREASING",
                    affected_fields=(f"{prefix}.top_depth_m", f"{prefix}.bottom_depth_m"),
                    reason="bottom_depth_m must be greater than top_depth_m",
                    observed={"top_depth_m": str(top), "bottom_depth_m": str(bottom)},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="no complete top/bottom pairs")


class ThicknessConsistencyConstraint(GeologicalConstraint):
    name = "C2_thickness_consistency"

    def __init__(self, tolerance_m: Decimal | str = "0.05", severity: str = "warning") -> None:
        self.tolerance_m = Decimal(str(tolerance_m))
        if self.tolerance_m < 0:
            raise ValueError("thickness tolerance must be non-negative")
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index, item in enumerate(intervals(record)):
            top = as_decimal(item.get("top_depth_m"))
            bottom = as_decimal(item.get("bottom_depth_m"))
            thickness = as_decimal(item.get("thickness_m"))
            if top is None or bottom is None or thickness is None:
                continue
            evaluated += 1
            error = abs(thickness - (bottom - top))
            if error > self.tolerance_m:
                prefix = f"intervals[{index}]"
                violations.append(ConstraintViolation(
                    code="THICKNESS_MISMATCH",
                    affected_fields=(f"{prefix}.top_depth_m", f"{prefix}.bottom_depth_m", f"{prefix}.thickness_m"),
                    reason=f"absolute thickness error {error} m exceeds tolerance {self.tolerance_m} m",
                    observed={"reported_m": str(thickness), "calculated_m": str(bottom - top), "error_m": str(error)},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="no complete top/bottom/thickness triples")


class ContinuityConstraint(GeologicalConstraint):
    name = "C3_interval_continuity"

    def __init__(self, tolerance_m: Decimal | str = "0.05", severity: str = "warning") -> None:
        self.tolerance_m = Decimal(str(tolerance_m))
        if self.tolerance_m < 0:
            raise ValueError("continuity tolerance must be non-negative")
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        values = intervals(record)
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index in range(len(values) - 1):
            bottom = as_decimal(values[index].get("bottom_depth_m"))
            next_top = as_decimal(values[index + 1].get("top_depth_m"))
            if bottom is None or next_top is None:
                continue
            evaluated += 1
            delta = next_top - bottom
            if abs(delta) > self.tolerance_m:
                kind = "GAP" if delta > 0 else "OVERLAP"
                violations.append(ConstraintViolation(
                    code=f"INTERVAL_{kind}",
                    affected_fields=(f"intervals[{index}].bottom_depth_m", f"intervals[{index + 1}].top_depth_m"),
                    reason=f"{kind.lower()} {abs(delta)} m exceeds tolerance {self.tolerance_m} m",
                    observed={"previous_bottom_m": str(bottom), "next_top_m": str(next_top), "signed_delta_m": str(delta)},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="fewer than two adjacent complete intervals")


class MonotonicityConstraint(GeologicalConstraint):
    name = "C4_depth_monotonicity"

    def __init__(self, tolerance_m: Decimal | str = "0.00", severity: str = "error") -> None:
        self.tolerance_m = Decimal(str(tolerance_m))
        if self.tolerance_m < 0:
            raise ValueError("monotonicity tolerance must be non-negative")
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        values = intervals(record)
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index in range(len(values) - 1):
            top = as_decimal(values[index].get("top_depth_m"))
            bottom = as_decimal(values[index].get("bottom_depth_m"))
            next_top = as_decimal(values[index + 1].get("top_depth_m"))
            next_bottom = as_decimal(values[index + 1].get("bottom_depth_m"))
            if None in (top, bottom, next_top, next_bottom):
                continue
            evaluated += 1
            if next_top + self.tolerance_m < top or next_bottom + self.tolerance_m < bottom:
                violations.append(ConstraintViolation(
                    code="DEPTH_SEQUENCE_INVERSION",
                    affected_fields=(f"intervals[{index}]", f"intervals[{index + 1}]"),
                    reason="successive interval boundaries decrease with depth",
                    observed={"previous": [str(top), str(bottom)], "next": [str(next_top), str(next_bottom)]},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="fewer than two adjacent complete intervals")


class FinalDepthConsistencyConstraint(GeologicalConstraint):
    name = "C5_final_depth_consistency"

    def __init__(self, tolerance_m: Decimal | str = "0.05", severity: str = "warning") -> None:
        self.tolerance_m = Decimal(str(tolerance_m))
        if self.tolerance_m < 0:
            raise ValueError("final-depth tolerance must be non-negative")
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        final_depth = as_decimal(record.get("borehole", {}).get("final_depth_m"))
        interval_values = intervals(record)
        last_bottom = as_decimal(interval_values[-1].get("bottom_depth_m")) if interval_values else None
        violations: list[ConstraintViolation] = []
        evaluated = int(final_depth is not None and last_bottom is not None)
        if evaluated:
            error = abs(final_depth - last_bottom)
            if error > self.tolerance_m:
                violations.append(ConstraintViolation(
                    code="FINAL_DEPTH_MISMATCH",
                    affected_fields=("borehole.final_depth_m", f"intervals[{len(interval_values)-1}].bottom_depth_m"),
                    reason=f"last interval/final depth error {error} m exceeds tolerance {self.tolerance_m} m",
                    observed={"final_depth_m": str(final_depth), "last_bottom_m": str(last_bottom), "error_m": str(error)},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="final depth or last bottom is missing")
