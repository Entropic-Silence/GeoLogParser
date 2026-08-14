"""Conservative direct-text parsing of Swiss LV95 spatial metadata.

The parser emits a coordinate pair only when exactly one distinct, plausible
pair occurs after a coordinate-label token.  Multiple page values are treated
as ambiguous rather than resolved against an external database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


COORDINATE_LABEL = re.compile(r"(?:k|c)?oord(?:inaten?)?", re.IGNORECASE)
COLLAR_LABEL = re.compile(r"(?:bohr|terrain)kote", re.IGNORECASE)
CONFUSABLE_TRANSLATION = str.maketrans({"l": "1", "I": "1", "|": "1", "O": "0"})
GROUP_SEPARATORS = frozenset(" '’‘`.\u00a0")


@dataclass(frozen=True)
class SpatialTextPrediction:
    x_coordinate: float | None
    y_coordinate: float | None
    collar_elevation_m: float | None
    coordinate_source_text: str | None
    collar_source_text: str | None
    coordinate_status: str
    collar_status: str
    coordinate_candidate_count: int


def _seven_digit_values(text: str) -> list[int]:
    normalized = text.translate(CONFUSABLE_TRANSLATION)
    output: list[int] = []
    occupied_until = -1
    for start, character in enumerate(normalized):
        if start < occupied_until or character not in "12":
            continue
        digits = ""
        end = start
        for index in range(start, min(len(normalized), start + 30)):
            current = normalized[index]
            if current.isdigit():
                digits += current
                if len(digits) == 7:
                    end = index + 1
                    break
            elif current not in GROUP_SEPARATORS:
                break
        if len(digits) == 7:
            value = int(digits)
            if 1_000_000 <= value <= 2_999_999:
                output.append(value)
                occupied_until = end
    return output


def _coordinate_candidates(text: str) -> list[tuple[int, int, str]]:
    candidates: list[tuple[int, int, str]] = []
    for line in text.splitlines():
        label = COORDINATE_LABEL.search(line)
        if not label:
            continue
        # Dates and project numbers before the label are intentionally ignored.
        values = _seven_digit_values(line[label.start():])
        for first, second in zip(values, values[1:]):
            if 2_400_000 <= first <= 2_900_000 and 1_000_000 <= second <= 1_400_000:
                candidate = (first, second, line.strip())
                if candidate[:2] not in [existing[:2] for existing in candidates]:
                    candidates.append(candidate)
    return candidates


def _collar_candidates(text: str) -> list[tuple[float, str]]:
    candidates: list[tuple[float, str]] = []
    for line in text.splitlines():
        label = COLLAR_LABEL.search(line)
        if not label:
            continue
        # A line containing only "+/- 0.5 m" states survey tolerance, not the
        # elevation.  Restrict values to plausible Swiss terrain elevations.
        for match in re.finditer(r"(?<!\d)(\d{3}(?:[.,]\d+)?)\s*(?:m\b)?", line[label.end():], re.I):
            value = float(match.group(1).replace(",", "."))
            if 200 <= value <= 1_000:
                candidate = (value, line.strip())
                if value not in [existing[0] for existing in candidates]:
                    candidates.append(candidate)
    return candidates


def parse_swissgeol_spatial_text(text: str) -> SpatialTextPrediction:
    coordinate_candidates = _coordinate_candidates(text)
    collar_candidates = _collar_candidates(text)
    if len(coordinate_candidates) == 1:
        x_coordinate, y_coordinate, coordinate_text = coordinate_candidates[0]
        coordinate_status = "EXTRACTED_UNAMBIGUOUS"
    elif coordinate_candidates:
        x_coordinate = y_coordinate = None
        coordinate_text = None
        coordinate_status = "ABSTAIN_AMBIGUOUS_MULTIPLE_COORDINATES"
    else:
        x_coordinate = y_coordinate = None
        coordinate_text = None
        coordinate_status = "ABSTAIN_NO_COORDINATE_PAIR"
    if len(collar_candidates) == 1:
        collar_elevation, collar_text = collar_candidates[0]
        collar_status = "EXTRACTED_UNAMBIGUOUS"
    elif collar_candidates:
        collar_elevation = None
        collar_text = None
        collar_status = "ABSTAIN_AMBIGUOUS_MULTIPLE_ELEVATIONS"
    else:
        collar_elevation = None
        collar_text = None
        collar_status = "ABSTAIN_NO_EXPLICIT_ELEVATION"
    return SpatialTextPrediction(
        x_coordinate=float(x_coordinate) if x_coordinate is not None else None,
        y_coordinate=float(y_coordinate) if y_coordinate is not None else None,
        collar_elevation_m=collar_elevation,
        coordinate_source_text=coordinate_text,
        collar_source_text=collar_text,
        coordinate_status=coordinate_status,
        collar_status=collar_status,
        coordinate_candidate_count=len(coordinate_candidates),
    )
