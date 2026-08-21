"""Evidence attachment and conservative agreement for VLM proposals."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from geologparser.evaluation import match_intervals_by_boundaries


_NUMBER = re.compile(r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?![A-Za-z0-9])")


def numeric_region_evidence(
    regions: Sequence[Mapping[str, Any]],
    value: float,
    *,
    tolerance: float = 1e-6,
) -> list[dict[str, Any]]:
    """Return OCR regions that explicitly contain a requested source-unit value."""
    evidence: list[dict[str, Any]] = []
    for region in regions:
        text = str(region.get("text") or "")
        values = [float(token) for token in _NUMBER.findall(text.replace(",", ""))]
        if not any(abs(candidate - value) <= tolerance for candidate in values):
            continue
        evidence.append({
            "page_index": region.get("page_index"),
            "regions_path": region.get("regions_path"),
            "bbox": list(region["bbox"]),
            "confidence": float(region["confidence"]),
            "text": text,
        })
    return evidence


def agreeing_interval_pairs(
    proposals: Sequence[Mapping[str, Any]],
    positioned_candidates: Sequence[Mapping[str, Any]],
    *,
    tolerance_m: float = 1e-6,
) -> list[tuple[int, int]]:
    """Match complete intervals without repairing either reader's output."""
    matches, _, _ = match_intervals_by_boundaries(
        proposals, positioned_candidates, tolerance_m=tolerance_m,
    )
    return [(match.reference_index, match.prediction_index) for match in matches]


def monotonic_nonoverlapping_indices(
    intervals: Sequence[Mapping[str, Any]],
    candidate_indices: Sequence[int],
    *,
    tolerance_m: float = 1e-6,
) -> tuple[list[int], list[int]]:
    """Keep valid candidate intervals whose accepted subsequence never overlaps."""
    accepted: list[int] = []
    rejected: list[int] = []
    previous_bottom: float | None = None
    for index in candidate_indices:
        interval = intervals[index]
        top = float(interval["top_depth_m"])
        bottom = float(interval["bottom_depth_m"])
        valid = top >= 0.0 and bottom > top
        monotonic = previous_bottom is None or top >= previous_bottom - tolerance_m
        if not valid or not monotonic:
            rejected.append(index)
            continue
        accepted.append(index)
        previous_bottom = bottom
    return accepted, rejected
