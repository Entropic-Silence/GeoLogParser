"""C6–C10 range, format, sequence, and field-type constraints."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Mapping, Sequence

from .base import ConstraintViolation, GeologicalConstraint, as_decimal, intervals, make_result, unwrap


class GroundwaterReasonablenessConstraint(GeologicalConstraint):
    name = "C6_groundwater_reasonableness"

    def __init__(self, severity: str = "high_risk_warning") -> None:
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        borehole = record.get("borehole", {})
        water = as_decimal(borehole.get("groundwater_depth_m"))
        final_depth = as_decimal(borehole.get("final_depth_m"))
        violations: list[ConstraintViolation] = []
        evaluated = 0
        if water is not None:
            evaluated += 1
            if water < 0:
                violations.append(ConstraintViolation(
                    code="GROUNDWATER_NEGATIVE_DEPTH",
                    affected_fields=("borehole.groundwater_depth_m",),
                    reason="groundwater depth below ground is negative; verify whether the source uses elevation or an above-ground reference",
                    observed={"groundwater_depth_m": str(water)},
                ))
        if water is not None and final_depth is not None:
            evaluated += 1
            if water > final_depth:
                violations.append(ConstraintViolation(
                    code="GROUNDWATER_BELOW_FINAL_DEPTH",
                    affected_fields=("borehole.groundwater_depth_m", "borehole.final_depth_m"),
                    reason="groundwater depth exceeds final depth; definitions may differ, so review rather than overwrite",
                    observed={"groundwater_depth_m": str(water), "final_depth_m": str(final_depth)},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="groundwater depth is missing")


class PercentageRangeConstraint(GeologicalConstraint):
    name = "C7_percentage_range"

    def __init__(
        self,
        field_names: Sequence[str] = ("rqd_percent", "core_recovery_percent"),
        minimum: Decimal | str = "0",
        maximum: Decimal | str = "100",
        severity: str = "error",
    ) -> None:
        minimum_decimal = Decimal(str(minimum))
        maximum_decimal = Decimal(str(maximum))
        if minimum_decimal > maximum_decimal:
            raise ValueError("percentage minimum cannot exceed maximum")
        self.field_names = tuple(field_names)
        self.minimum = minimum_decimal
        self.maximum = maximum_decimal
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index, item in enumerate(intervals(record)):
            for field_name in self.field_names:
                value = as_decimal(item.get(field_name))
                if value is None:
                    continue
                evaluated += 1
                if value < self.minimum or value > self.maximum:
                    path = f"intervals[{index}].{field_name}"
                    violations.append(ConstraintViolation(
                        code="PERCENTAGE_OUT_OF_RANGE", affected_fields=(path,),
                        reason=(
                            f"{field_name} must be within [{self.minimum}, {self.maximum}] "
                            "under the configured percentage representation"
                        ),
                        observed={field_name: str(value)},
                    ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="no configured percentage values")


class CoordinateFormatConstraint(GeologicalConstraint):
    name = "C8_coordinate_format"

    def __init__(self, minimum_digits: int = 4, maximum_digits: int = 12, severity: str = "warning") -> None:
        self.minimum_digits = minimum_digits
        self.maximum_digits = maximum_digits
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        borehole = record.get("borehole", {})
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for name in ("x_coordinate", "y_coordinate", "collar_elevation_m"):
            envelope = borehole.get(name)
            if envelope is None:
                continue
            value = unwrap(envelope)
            raw = envelope.get("source_text") if isinstance(envelope, Mapping) else None
            if value is None and not raw:
                continue
            evaluated += 1
            raw_text = str(raw) if raw is not None else str(value)
            if re.search(r"[OoIl]", raw_text):
                violations.append(ConstraintViolation(
                    code="NUMERIC_OCR_CONFUSABLE", affected_fields=(f"borehole.{name}",),
                    reason="numeric source text contains O/0 or I/l/1 confusable characters",
                    observed={"source_text": raw_text, "value": value},
                    suggested_action="generate_numeric_ocr_candidates",
                ))
            digits = len(re.sub(r"\D", "", raw_text))
            minimum_digits = 1 if name == "collar_elevation_m" else self.minimum_digits
            if digits and not minimum_digits <= digits <= self.maximum_digits:
                violations.append(ConstraintViolation(
                    code="NUMERIC_DIGIT_LENGTH_SUSPICIOUS", affected_fields=(f"borehole.{name}",),
                    reason=f"numeric digit count {digits} is outside configured [{minimum_digits}, {self.maximum_digits}]",
                    observed={"source_text": raw_text, "digit_count": digits},
                ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="no coordinate/elevation evidence")


class StratumCodeSequenceConstraint(GeologicalConstraint):
    name = "C9_stratum_code_sequence"

    def __init__(self, severity: str = "weak_warning") -> None:
        self.severity = severity

    @staticmethod
    def _simple_integer(value: Any) -> int | None:
        text = str(value).strip() if value is not None else ""
        match = re.fullmatch(r"[①②③④⑤⑥⑦⑧⑨⑩]|\d+", text)
        if not match:
            return None
        circled = "①②③④⑤⑥⑦⑧⑨⑩"
        return circled.index(text) + 1 if text in circled else int(text)

    def evaluate(self, record: Mapping[str, Any]):
        values: list[tuple[int, int]] = []
        for index, item in enumerate(intervals(record)):
            parsed = self._simple_integer(unwrap(item.get("stratum_code_raw")))
            if parsed is not None:
                values.append((index, parsed))
        violations: list[ConstraintViolation] = []
        for (left_index, left), (right_index, right) in zip(values, values[1:]):
            if right == left:
                code, reason = "STRATUM_CODE_DUPLICATE", "adjacent simple stratum codes are duplicated"
            elif right != left + 1:
                code, reason = "STRATUM_CODE_JUMP", "simple stratum code sequence contains a jump or reversal"
            else:
                continue
            violations.append(ConstraintViolation(
                code=code,
                affected_fields=(f"intervals[{left_index}].stratum_code_raw", f"intervals[{right_index}].stratum_code_raw"),
                reason=reason,
                observed={"previous": left, "next": right},
                suggested_action="weak_review_only",
            ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=max(0, len(values) - 1),
                           violations=violations, not_evaluated_reason="fewer than two simple stratum codes")


class FieldTypeConsistencyConstraint(GeologicalConstraint):
    name = "C10_field_type_consistency"
    NUMERIC_TEXT = re.compile(r"^\s*[-+]?\d+(?:\.\d+)?\s*(?:m|米)?\s*$", re.I)
    GEOLOGICAL_TEXT = re.compile(r"[\u4e00-\u9fff]|clay|sand|silt|rock|mudstone|sandstone|gravel|fill", re.I)

    def __init__(self, severity: str = "error") -> None:
        self.severity = severity

    def evaluate(self, record: Mapping[str, Any]):
        violations: list[ConstraintViolation] = []
        evaluated = 0
        for index, item in enumerate(intervals(record)):
            for field_name in ("lithology_raw", "description_raw"):
                value = unwrap(item.get(field_name))
                if value is None:
                    continue
                evaluated += 1
                if self.NUMERIC_TEXT.fullmatch(str(value)):
                    path = f"intervals[{index}].{field_name}"
                    violations.append(ConstraintViolation(
                        code="TEXT_FIELD_CONTAINS_NUMERIC_VALUE", affected_fields=(path,),
                        reason="geological text field contains only a numeric value, suggesting column misalignment",
                        observed={field_name: value}, suggested_action="review_layout_assignment",
                    ))
            for field_name in ("top_depth_m", "bottom_depth_m", "thickness_m"):
                envelope = item.get(field_name)
                value = unwrap(envelope)
                raw = envelope.get("source_text") if isinstance(envelope, Mapping) else value
                if raw is None:
                    continue
                evaluated += 1
                if as_decimal(value) is None and self.GEOLOGICAL_TEXT.search(str(raw)):
                    path = f"intervals[{index}].{field_name}"
                    violations.append(ConstraintViolation(
                        code="NUMERIC_FIELD_CONTAINS_GEOLOGICAL_TEXT", affected_fields=(path,),
                        reason="depth/thickness field contains geological text, suggesting column misalignment",
                        observed={"source_text": raw, "value": value}, suggested_action="review_layout_assignment",
                    ))
        return make_result(name=self.name, severity=self.severity, evaluated_count=evaluated,
                           violations=violations, not_evaluated_reason="no interval field values")
