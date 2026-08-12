"""Deterministic error taxonomy assignment and distribution summaries."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


ERROR_TAXONOMY_V001 = (
    "OCR_digit_error", "OCR_character_error", "decimal_point_error",
    "column_misalignment", "row_merge", "row_split", "interval_boundary_error",
    "missing_interval", "duplicate_interval", "lithology_semantic_error",
    "normalization_error", "hallucination", "layout_error",
    "constraint_false_positive", "constraint_false_negative", "re_read_failure",
)


def classify_field_error(field: str, reference: Any, prediction: Any) -> str | None:
    """Assign only high-confidence classes; ambiguous cases remain unclassified."""
    if reference == prediction:
        return None
    if reference in (None, "") and prediction not in (None, ""):
        return "hallucination"
    if field == "intervals" and prediction in (None, [], 0):
        return "missing_interval"
    if field in {"top_depth_m", "bottom_depth_m", "thickness_m"}:
        return "interval_boundary_error"
    if "normalized" in field:
        return "normalization_error"
    if "lithology" in field:
        return "lithology_semantic_error"
    reference_text = str(reference)
    prediction_text = "" if prediction is None else str(prediction)
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", reference_text):
        if reference_text.replace(".", "") == prediction_text.replace(".", ""):
            return "decimal_point_error"
        return "OCR_digit_error"
    if prediction is None:
        return None
    return "OCR_character_error"


def error_distribution(
    errors: Iterable[Mapping[str, Any]],
    taxonomy: Sequence[str] = ERROR_TAXONOMY_V001,
) -> dict[str, Any]:
    """Count known and unknown labels without silently discarding either."""
    allowed = tuple(taxonomy)
    counter = Counter(str(error.get("error_type", "UNCLASSIFIED")) for error in errors)
    known_total = sum(counter[name] for name in allowed)
    unknown = {name: count for name, count in sorted(counter.items()) if name not in allowed}
    total = sum(counter.values())
    return {
        "total": total,
        "known_total": known_total,
        "known_coverage": known_total / total if total else None,
        "counts": {name: counter[name] for name in allowed},
        "rates": {name: counter[name] / total if total else None for name in allowed},
        "unknown": unknown,
    }
