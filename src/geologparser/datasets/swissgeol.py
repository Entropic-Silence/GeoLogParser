"""Deterministic parsing helpers for Swissgeol drilling-protocol tables."""

from __future__ import annotations

import re


NUMBER = r"\d+(?:[.,]\d+)?"
RANGE = re.compile(
    rf"^\s*({NUMBER})\s*(?:m\s*)?[-–—]\s*({NUMBER})\s*m?\b", re.I,
)
BOUNDARY = re.compile(rf"^\s*({NUMBER})\s*m?(?:\s+|$)", re.I)


def _normalize_numeric_ocr(text: str) -> str:
    text = re.sub(r"^\s*[|}\]\[]+\s*(?=\d)", "", text)
    text = re.sub(r"(?<=\d)[lI](?=\s*m?\s*[-–—])", "1", text)
    text = re.sub(r"(?<=[-–—])[lI](?=\s*m?\b)", "1", text)
    return re.sub(r"^\s*[lI](?=\s*[-–—])", "1", text)


def explicit_interval_sections(
    text: str, final_depth_m: float | None = None,
) -> list[list[tuple[float, float]]]:
    """Extract conservative interval candidates from explicit protocol tables."""
    lines = text.splitlines()
    starts = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        if (
            re.search(r"\bbis\s+tiefe\b", lowered)
            or re.search(r"\bbis\s+tief(?:e|em)?\b", lowered)
            or re.match(r"^\s*bis\s+m\b", lowered)
            or (
                re.search(r"\b(?:tiefe\s*m|tiefem)\b", lowered)
                and re.search(r"beschreibung.*bohrgut", lowered)
            )
            or re.search(r"beschreibung.*bohrgut", lowered)
        ):
            starts.append(index)
    sections: list[list[tuple[float, float]]] = []
    for start in starts:
        ranges: list[tuple[float, float]] = []
        boundaries: list[float] = []
        started = False
        blank_count = 0
        for raw_line in lines[start + 1:start + 56]:
            line = _normalize_numeric_ocr(raw_line)
            if started and re.search(
                r"grundwasser|bohrkote|verrohrung|bohrmeissel|bohrwerkzeug|hydrologie",
                line, re.I,
            ):
                break
            if not line.strip():
                blank_count += int(started)
                if started and blank_count >= 4:
                    break
                continue
            match = RANGE.match(line)
            if match:
                top, bottom = (float(value.replace(",", ".")) for value in match.groups())
                if 0 <= top < bottom and (
                    final_depth_m is None or bottom <= final_depth_m + 1e-6
                ):
                    ranges.append((top, bottom))
                    started, blank_count = True, 0
                continue
            match = BOUNDARY.match(line)
            if match:
                boundary = float(match.group(1).replace(",", "."))
                remainder = line[match.end():]
                if (
                    0 < boundary
                    and (final_depth_m is None or boundary <= final_depth_m + 1e-6)
                    and (not remainder.strip() or re.search(r"[A-Za-zÄÖÜäöüß]", remainder))
                ):
                    boundaries.append(boundary)
                    started, blank_count = True, 0
        if ranges:
            candidate = sorted(set(ranges))
        elif boundaries:
            ordered: list[float] = []
            for boundary in boundaries:
                if not ordered or boundary != ordered[-1]:
                    ordered.append(boundary)
                if final_depth_m is not None and abs(boundary - final_depth_m) <= 1e-6:
                    break
            increasing = []
            for boundary in ordered:
                if not increasing or boundary > increasing[-1]:
                    increasing.append(boundary)
            values = [0.0, *increasing]
            candidate = [
                (values[index], values[index + 1])
                for index in range(len(values) - 1)
                if values[index] < values[index + 1]
            ]
        else:
            continue
        if candidate and candidate not in sections:
            sections.append(candidate)
    return sections


def choose_interval_section(
    text: str, final_depth_m: float | None = None,
) -> list[tuple[float, float]]:
    sections = explicit_interval_sections(text, final_depth_m)
    return max(
        sections,
        key=lambda section: (
            final_depth_m is not None and abs(section[-1][1] - final_depth_m) <= 1e-6,
            len(section),
        ),
        default=[],
    )
