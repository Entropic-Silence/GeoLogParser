"""Public API for non-mutating geological constraints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ConstraintViolation:
    code: str
    affected_fields: tuple[str, ...]
    reason: str
    observed: Mapping[str, Any] = field(default_factory=dict)
    suggested_action: str = "review_source_evidence"


@dataclass(frozen=True)
class ConstraintResult:
    name: str
    status: str
    passed: bool
    score: float | None
    severity: str
    affected_fields: tuple[str, ...]
    reason: str
    suggested_action: str
    evaluated_count: int
    violations: tuple[ConstraintViolation, ...] = ()


class GeologicalConstraint(ABC):
    """A constraint evaluates evidence but never mutates a record."""

    name: str
    severity: str

    @abstractmethod
    def evaluate(self, record: Mapping[str, Any]) -> ConstraintResult:
        raise NotImplementedError


def unwrap(field_value: Any) -> Any:
    """Read either a schema envelope or a plain value for test/integration use."""
    if isinstance(field_value, Mapping) and "value" in field_value:
        return field_value["value"]
    return field_value


def as_decimal(field_value: Any) -> Decimal | None:
    value = unwrap(field_value)
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def intervals(record: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    value = record.get("intervals", ())
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def make_result(
    *,
    name: str,
    severity: str,
    evaluated_count: int,
    violations: list[ConstraintViolation],
    not_evaluated_reason: str,
) -> ConstraintResult:
    if evaluated_count == 0:
        return ConstraintResult(
            name=name,
            status="not_evaluated",
            passed=True,
            score=None,
            severity=severity,
            affected_fields=(),
            reason=not_evaluated_reason,
            suggested_action="none",
            evaluated_count=0,
        )
    affected = tuple(dict.fromkeys(f for v in violations for f in v.affected_fields))
    passed = not violations
    return ConstraintResult(
        name=name,
        status="passed" if passed else "violated",
        passed=passed,
        score=max(0.0, 1.0 - len(violations) / evaluated_count),
        severity=severity,
        affected_fields=affected,
        reason="passed" if passed else f"{len(violations)} of {evaluated_count} evaluations violated",
        suggested_action="none" if passed else "constraint_guided_reread",
        evaluated_count=evaluated_count,
        violations=tuple(violations),
    )
