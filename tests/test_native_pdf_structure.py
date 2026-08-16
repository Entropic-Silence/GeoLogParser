from pathlib import Path

import pytest

from geologparser.layout.native_pdf_structure import (
    NativePDFWord, _numeric_columns, parse_native_number,
)


def word(text: str, x: float, y: float, block: int = 0) -> NativePDFWord:
    return NativePDFWord(1, text, (x, y, x + 5, y + 2), x / 100, y / 100, block, 0)


@pytest.mark.parametrize(("text", "expected"), [("4.50", 4.5), ("1'037.39", 1037.39), ("12,5", 12.5)])
def test_parse_native_number(text: str, expected: float):
    assert parse_native_number(text) == expected


def test_numeric_column_prefers_semantically_anchored_depth_sequence():
    words = [
        word("Depth", 20, 5, 1), word("interval", 20, 7, 1),
        word("1.0", 20, 20), word("2.5", 20, 30), word("4.0", 20, 40),
        word("100", 80, 20), word("200", 80, 30), word("300", 80, 40),
    ]
    columns = _numeric_columns(words, page_range=(0.0, 4.0), x_tolerance=0.02)
    assert columns[0].header_role == "cumulative_depth"
    assert columns[0].values == (1.0, 2.5, 4.0)
