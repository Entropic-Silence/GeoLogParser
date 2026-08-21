"""Deterministic interval decoding for MinerU table elements.

MinerU's official two-step parser emits page elements whose table content is
HTML.  This module intentionally uses only declared table headers and numeric
cells; it never fills a missing boundary from thickness, adjacent rows or a
reference record.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any, Mapping, Sequence


class _HTMLTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._table is not None and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def html_tables(markup: str) -> list[list[list[str]]]:
    parser = _HTMLTableParser()
    parser.feed(markup)
    parser.close()
    return parser.tables


_NUMBER = re.compile(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:ft|feet|m|metres?|meters?)?\s*$", re.IGNORECASE)


def _number(cell: str) -> float | None:
    match = _NUMBER.fullmatch(cell)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _column_index(headers: Sequence[str], terms: set[str]) -> int | None:
    for index, header in enumerate(headers):
        words = set(re.findall(r"[a-z]+", header.lower()))
        if terms & words:
            return index
    return None


def decode_mineru_intervals(
    elements: Sequence[Mapping[str, Any]], *, scale_to_m: float,
) -> tuple[list[dict[str, Any]], int, int]:
    """Decode explicitly labelled top/bottom table cells.

    Returns accepted intervals, rejected numeric-like rows and the number of
    discovered table elements.  When headers are unavailable, no interval is
    emitted rather than guessing column ownership.
    """
    intervals: list[dict[str, Any]] = []
    rejected = 0
    table_count = 0
    for element in elements:
        if str(element.get("type") or "").lower() != "table":
            continue
        content = element.get("content")
        if not isinstance(content, str):
            continue
        for table in html_tables(content):
            table_count += 1
            if len(table) < 2:
                continue
            headers = table[0]
            top_index = _column_index(headers, {"top", "from", "start"})
            bottom_index = _column_index(headers, {"bottom", "to", "end"})
            lithology_index = _column_index(headers, {"lithology", "material", "description", "stratum"})
            if top_index is None or bottom_index is None or top_index == bottom_index:
                continue
            for row in table[1:]:
                if len(row) <= max(top_index, bottom_index):
                    rejected += 1
                    continue
                top, bottom = _number(row[top_index]), _number(row[bottom_index])
                if top is None or bottom is None or top < 0 or bottom <= top:
                    rejected += 1
                    continue
                lithology = row[lithology_index].strip() if lithology_index is not None and lithology_index < len(row) else None
                intervals.append({
                    "top_depth_m": top * scale_to_m,
                    "bottom_depth_m": bottom * scale_to_m,
                    "thickness_m": (bottom - top) * scale_to_m,
                    "lithology_raw": lithology or None,
                })
    return intervals, rejected, table_count
