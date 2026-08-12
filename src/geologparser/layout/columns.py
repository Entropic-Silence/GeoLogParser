"""Conservative positioned-text column analysis for native borehole logs."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from geologparser.io.records import empty_interval, field
from geologparser.ocr import TextRegion


DEPTH_RANGE = re.compile(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)(?!\d)")


@dataclass(frozen=True)
class DepthRangeCandidate:
    page: int
    bbox: tuple[float, float, float, float]
    top_m: float
    bottom_m: float
    source_text: str


def _candidates(regions: Sequence[TextRegion]) -> list[DepthRangeCandidate]:
    candidates = []
    for region in regions:
        if region.bbox is None:
            continue
        for match in DEPTH_RANGE.finditer(region.text):
            top = float(match.group(1).replace(",", "."))
            bottom = float(match.group(2).replace(",", "."))
            if 0 <= top < bottom and bottom - top <= 1000:
                candidates.append(DepthRangeCandidate(
                    region.page, region.bbox, top, bottom, match.group(0),
                ))
    return candidates


def extract_depth_column_intervals(
    regions: Sequence[TextRegion], *, x_bin_points: float = 12.0, minimum_unique_ranges: int = 3,
) -> list[dict]:
    """Extract a repeated positioned depth-range column and nearby descriptions.

    The dominant x bin must contain at least ``minimum_unique_ranges`` distinct
    boundaries. This intentionally abstains on pages where depths are vector
    graphics or where isolated ranges occur only inside prose/sample labels.
    """
    if x_bin_points <= 0 or minimum_unique_ranges < 2:
        raise ValueError("x_bin_points must be positive and minimum_unique_ranges at least two")
    candidates = _candidates(regions)
    bins: dict[tuple[int, int], list[DepthRangeCandidate]] = defaultdict(list)
    for candidate in candidates:
        bins[(candidate.page, round(candidate.bbox[0] / x_bin_points))].append(candidate)
    eligible = []
    for key, values in bins.items():
        unique = {(item.top_m, item.bottom_m) for item in values}
        if len(unique) >= minimum_unique_ranges:
            eligible.append((len(unique), -key[1], key, values))
    if not eligible:
        return []
    _, _, dominant_key, values = max(eligible)
    page = dominant_key[0]
    # Deduplicate repeated sample and main-column text for the same boundary.
    by_range: dict[tuple[float, float], DepthRangeCandidate] = {}
    for candidate in sorted(values, key=lambda item: (item.bbox[1], item.bbox[0])):
        by_range.setdefault((candidate.top_m, candidate.bottom_m), candidate)
    ordered = sorted(by_range.values(), key=lambda item: (item.top_m, item.bottom_m, item.bbox[1]))
    # Require non-decreasing geological order; a conflicting cluster is unsafe.
    if any(current.top_m < previous.top_m for previous, current in zip(ordered, ordered[1:])):
        return []
    column_x = sum(item.bbox[0] for item in ordered) / len(ordered)
    page_regions = [region for region in regions if region.page == page and region.bbox is not None]
    intervals = []
    previous_y = min((region.bbox[1] for region in page_regions), default=0.0)
    for index, candidate in enumerate(ordered, 1):
        boundary_y = (candidate.bbox[1] + candidate.bbox[3]) / 2
        description_regions = [
            region for region in page_regions
            if region.bbox[0] > column_x + 20
            and previous_y <= (region.bbox[1] + region.bbox[3]) / 2 <= boundary_y + 2
            and not any(token in region.text.lower() for token in ("legend", "borehole:", "municipality:", "description"))
        ]
        description = " ".join(" ".join(region.text.split()) for region in description_regions).strip() or None
        description_bbox = None
        if description_regions:
            description_bbox = [
                min(region.bbox[0] for region in description_regions),
                min(region.bbox[1] for region in description_regions),
                max(region.bbox[2] for region in description_regions),
                max(region.bbox[3] for region in description_regions),
            ]
        interval = empty_interval(f"I{index:03d}")
        provenance = dict(
            source_page=candidate.page, source_bbox=list(candidate.bbox),
            extraction_method="layout", confidence=None,
            validation_status="needs_review", warning_codes=["LAYOUT_RULE_UNVERIFIED"], raw_unit="m",
        )
        interval["top_depth_m"] = field(candidate.top_m, source_text=candidate.source_text, **provenance)
        interval["bottom_depth_m"] = field(candidate.bottom_m, source_text=candidate.source_text, **provenance)
        interval["thickness_m"] = field(
            round(candidate.bottom_m - candidate.top_m, 6), source_text=candidate.source_text,
            source_page=candidate.page, source_bbox=list(candidate.bbox), extraction_method="derived",
            confidence=None, validation_status="needs_review", warning_codes=["DERIVED_FROM_LAYOUT_BOUNDARIES"], raw_unit="m",
        )
        if description is not None:
            interval["description_raw"] = field(
                description, source_page=candidate.page, source_bbox=description_bbox,
                source_text=description, extraction_method="layout", confidence=None,
                validation_status="needs_review", warning_codes=["LAYOUT_RULE_UNVERIFIED"],
            )
        intervals.append(interval)
        previous_y = boundary_y
    return intervals
