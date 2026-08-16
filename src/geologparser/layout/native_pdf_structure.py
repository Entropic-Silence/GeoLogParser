"""Reference-blind structural evidence extraction from native PDF word boxes.

Long engineering logs often retain a precise vector text layer even when a
low-resolution raster OCR pass recovers almost no usable depth tokens.  This
module treats that layer as another modality: it locates semantic depth-column
headers, groups numeric words by x position, and reconstructs monotonic depth
sequences.  It never consumes reference intervals.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import re
from statistics import median
from typing import Sequence


@dataclass(frozen=True)
class NativePDFWord:
    page: int
    text: str
    bbox: tuple[float, float, float, float]
    x_norm: float
    y_norm: float
    block: int
    line: int


@dataclass(frozen=True)
class NativeNumericColumn:
    page: int
    x_norm: float
    values: tuple[float, ...]
    words: tuple[NativePDFWord, ...]
    header_role: str | None
    header_distance: float | None
    monotonic_ratio: float
    span_m: float
    scale_tick_score: float
    range_support: float
    score: float


@dataclass(frozen=True)
class NativeStructuralPrediction:
    status: str
    reason: str
    boundaries: tuple[float, ...]
    selected_columns: tuple[NativeNumericColumn, ...]
    candidates: tuple[NativeNumericColumn, ...]
    document_signals: tuple[str, ...]
    risk_score: float

    def to_dict(self) -> dict:
        return asdict(self)


_NUMBER = re.compile(
    r"^\s*[([]?([0-9]{1,4}(?:['\N{RIGHT SINGLE QUOTATION MARK}][0-9]{3})?(?:[.,][0-9]{1,3})?)[)\]]?\s*(?:m)?\s*$",
    re.I,
)
_RANGE = re.compile(
    r"([0-9]{1,4}(?:['\N{RIGHT SINGLE QUOTATION MARK}][0-9]{3})?(?:[.,][0-9]{1,3})?)\s*m?\s*[-\N{EN DASH}\N{EM DASH}]\s*"
    r"([0-9]{1,4}(?:['\N{RIGHT SINGLE QUOTATION MARK}][0-9]{3})?(?:[.,][0-9]{1,3})?)\s*m",
    re.I,
)

_HEADER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("cumulative_depth", re.compile(r"depth\s*interval|teufen?intervall|intervalle?\s+de\s+profondeur", re.I)),
    ("cumulative_depth", re.compile(r"\bmetres?\b|\bmeter\b|\btiefe\b|\bteufe\b|\bprofondeur\b", re.I)),
    ("thickness", re.compile(r"\bthickness\b|\bm(?:ä|ae)chtigkeit\b|\b(?:é|e)paisseur\b", re.I)),
)


def parse_native_number(text: str) -> float | None:
    """Parse a standalone depth-like token while retaining strict boundaries."""
    normalized = text.strip().replace("’", "'").replace(",", ".")
    match = _NUMBER.fullmatch(normalized)
    if not match:
        return None
    try:
        value = float(match.group(1).replace("'", ""))
    except ValueError:
        return None
    return value if 0.0 <= value <= 5000.0 else None


def _parse_range_value(text: str) -> float:
    return float(text.replace("’", "").replace("'", "").replace(",", "."))


def _longest_increasing(words: Sequence[tuple[NativePDFWord, float]]) -> list[tuple[NativePDFWord, float]]:
    if not words:
        return []
    ordered = sorted(words, key=lambda item: item[0].y_norm)
    lengths = [1] * len(ordered)
    previous = [-1] * len(ordered)
    for index in range(len(ordered)):
        for prior in range(index):
            if ordered[prior][1] < ordered[index][1] and lengths[prior] + 1 > lengths[index]:
                lengths[index] = lengths[prior] + 1
                previous[index] = prior
    end = max(range(len(ordered)), key=lambda index: (lengths[index], ordered[index][1]))
    output: list[tuple[NativePDFWord, float]] = []
    while end >= 0:
        output.append(ordered[end])
        end = previous[end]
    return list(reversed(output))


def _scale_tick_score(values: Sequence[float]) -> float:
    if len(values) < 5:
        return 0.0
    differences = [round(right - left, 3) for left, right in zip(values, values[1:]) if right > left]
    if not differences:
        return 0.0
    common = median(differences)
    if common <= 0:
        return 0.0
    regular = sum(abs(value - common) <= max(0.01, common * 0.03) for value in differences) / len(differences)
    round_values = sum(abs(value - round(value)) <= 1e-6 for value in values) / len(values)
    return regular * round_values


def _document_range(text: str) -> tuple[float, float] | None:
    candidates = []
    for match in _RANGE.finditer(text):
        left, right = _parse_range_value(match.group(1)), _parse_range_value(match.group(2))
        if 0 <= left < right <= 5000:
            candidates.append((right - left, left, right))
    if not candidates:
        return None
    _, left, right = max(candidates)
    return left, right


def extract_native_pdf_words(
    path: Path, *, pages: set[int] | None = None,
) -> tuple[list[NativePDFWord], dict[int, tuple[float, float]]]:
    """Return native PDF words in original point coordinates and normalized space."""
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - exercised by optional-dependency environments
        raise RuntimeError("native PDF structural extraction requires PyMuPDF") from exc
    output: list[NativePDFWord] = []
    dimensions: dict[int, tuple[float, float]] = {}
    with pymupdf.open(path) as document:
        for page_index, page in enumerate(document, 1):
            if pages is not None and page_index not in pages:
                continue
            width, height = float(page.rect.width), float(page.rect.height)
            dimensions[page_index] = (width, height)
            for item in page.get_text("words", sort=False):
                x0, y0, x1, y1, text, block, line, _ = item
                output.append(NativePDFWord(
                    page=page_index,
                    text=str(text),
                    bbox=(float(x0), float(y0), float(x1), float(y1)),
                    x_norm=((float(x0) + float(x1)) / 2.0) / width,
                    y_norm=((float(y0) + float(y1)) / 2.0) / height,
                    block=int(block),
                    line=int(line),
                ))
    return output, dimensions


def locate_named_log_pages(path: Path, target_name: str) -> tuple[int, ...]:
    """Locate report pages for a borehole alias without using interval labels.

    Multi-log reports are common in the public transfer corpus.  The official
    pairing supplies a borehole name such as ``Sondierungen Egnach KB3`` while
    the page title contains ``Kernbohrung KB3``.  Only the identity suffix is
    used here; no depth or lithology value participates in page selection.
    """
    aliases = {
        re.sub(r"[^A-Z0-9]", "", match.group(0).upper())
        for match in re.finditer(r"\b(?:KB|BS|BH|B|S)\s*-?\s*\d+[A-Z]?\b", target_name, re.I)
    }
    if not aliases:
        return ()
    words, _ = extract_native_pdf_words(path)
    by_page: dict[int, list[str]] = {}
    for word in words:
        # Titles and identifiers occur in the upper part of a log page.  A
        # full-page fallback remains useful for rotated title text.
        by_page.setdefault(word.page, []).append(word.text)
    matched = []
    for page, tokens in by_page.items():
        normalized = re.sub(r"[^A-Z0-9]", "", " ".join(tokens).upper())
        if any(alias in normalized for alias in aliases):
            matched.append(page)
    return tuple(sorted(matched))


def _headers(words: Sequence[NativePDFWord]) -> list[tuple[str, float, int, str]]:
    grouped: dict[tuple[int, int], list[NativePDFWord]] = {}
    for word in words:
        grouped.setdefault((word.page, word.block), []).append(word)
    output = []
    for (page, _), group in grouped.items():
        text = " ".join(word.text for word in sorted(group, key=lambda item: (item.line, item.x_norm)))
        center = sum(word.x_norm for word in group) / len(group)
        for role, pattern in _HEADER_PATTERNS:
            if pattern.search(text):
                output.append((role, center, page, text))
    return output


def _numeric_columns(
    words: Sequence[NativePDFWord], *, page_range: tuple[float, float] | None,
    x_tolerance: float,
) -> list[NativeNumericColumn]:
    headers = _headers(words)
    numeric = [(word, value) for word in words if (value := parse_native_number(word.text)) is not None]
    output: list[NativeNumericColumn] = []
    for page in sorted({word.page for word, _ in numeric}):
        page_numeric = sorted((item for item in numeric if item[0].page == page), key=lambda item: item[0].x_norm)
        clusters: list[list[tuple[NativePDFWord, float]]] = []
        for item in page_numeric:
            if not clusters or item[0].x_norm - clusters[-1][-1][0].x_norm > x_tolerance:
                clusters.append([item])
            else:
                clusters[-1].append(item)
        page_headers = [item for item in headers if item[2] == page]
        for cluster in clusters:
            by_y: list[tuple[NativePDFWord, float]] = []
            for item in sorted(cluster, key=lambda row: row[0].y_norm):
                if by_y and abs(item[0].y_norm - by_y[-1][0].y_norm) <= 0.0008:
                    # Prefer the token carrying greater decimal specificity.
                    if len(item[0].text) > len(by_y[-1][0].text):
                        by_y[-1] = item
                else:
                    by_y.append(item)
            sequence = _longest_increasing(by_y)
            if len(sequence) < 2:
                continue
            values = [item[1] for item in sequence]
            x_norm = sum(item[0].x_norm for item in cluster) / len(cluster)
            role_matches = sorted(
                ((abs(x_norm - center), role) for role, center, _, _ in page_headers),
                key=lambda item: item[0],
            )
            header_distance, header_role = role_matches[0] if role_matches else (None, None)
            if header_distance is not None and header_distance > 0.055:
                header_distance, header_role = None, None
            scale = _scale_tick_score(values)
            if page_range:
                left, right = page_range
                range_support = sum(left - 0.1 <= value <= right + 0.1 for value in values) / len(values)
            else:
                range_support = 1.0
            monotonic_ratio = sum(right > left for left, right in zip(values, values[1:])) / max(1, len(values) - 1)
            role_bonus = 8.0 if header_role == "cumulative_depth" else (-5.0 if header_role == "thickness" else 0.0)
            distance_bonus = 4.0 * max(0.0, 1.0 - (header_distance or 0.055) / 0.055) if header_role else 0.0
            score = (
                len(values)
                + 6.0 * monotonic_ratio
                + 3.0 * math.log1p((max(values) - min(values)) / 10.0)
                + 5.0 * range_support
                + role_bonus
                + distance_bonus
                - 12.0 * scale
            )
            output.append(NativeNumericColumn(
                page=page,
                x_norm=x_norm,
                values=tuple(values),
                words=tuple(item[0] for item in sequence),
                header_role=header_role,
                header_distance=header_distance,
                monotonic_ratio=monotonic_ratio,
                span_m=max(values) - min(values),
                scale_tick_score=scale,
                range_support=range_support,
                score=score,
            ))
    return sorted(output, key=lambda item: item.score, reverse=True)


def predict_native_pdf_boundaries(
    path: Path, *, x_tolerance: float = 0.008, pages: set[int] | None = None,
) -> NativeStructuralPrediction:
    """Recover a conservative boundary sequence from native PDF semantics."""
    words, _ = extract_native_pdf_words(path, pages=pages)
    joined = " ".join(word.text for word in words)
    lowered = joined.lower()
    signals = []
    if "lithostratigraphy" in lowered or "lithostratigraphie" in lowered:
        signals.append("lithostratigraphic_document")
    if "structural geology plot" in lowered:
        signals.append("structural_geology_document")
    page_range = _document_range(joined)
    if page_range:
        signals.append("explicit_document_depth_range")
    if "structural_geology_document" in signals and "lithostratigraphic_document" not in signals:
        return NativeStructuralPrediction(
            status="abstained", reason="structural_geology_not_stratigraphic_intervals",
            boundaries=(), selected_columns=(), candidates=(),
            document_signals=tuple(signals), risk_score=1.0,
        )
    candidates = _numeric_columns(words, page_range=page_range, x_tolerance=x_tolerance)
    anchored = [
        item for item in candidates
        if item.header_role == "cumulative_depth"
        and item.header_distance is not None and item.header_distance <= 0.03
        and item.scale_tick_score < 0.92 and len(item.values) >= 2
    ]
    if not anchored:
        return NativeStructuralPrediction(
            status="abstained", reason="no_semantically_anchored_depth_column",
            boundaries=(), selected_columns=(), candidates=tuple(candidates[:12]),
            document_signals=tuple(signals), risk_score=1.0,
        )
    selected = max(anchored, key=lambda item: item.score)
    boundaries = list(selected.values)
    if page_range:
        left, right = page_range
        if not boundaries or boundaries[0] > left + 0.05:
            boundaries.insert(0, left)
        if boundaries and boundaries[-1] < right - 0.05 and right - boundaries[-1] <= max(5.0, (right - left) * 0.1):
            boundaries.append(right)
    elif boundaries and boundaries[0] > 0.05:
        boundaries.insert(0, 0.0)
    boundaries = sorted({round(value, 6) for value in boundaries})
    margin = selected.score - max((item.score for item in candidates if item is not selected), default=selected.score)
    risk = min(1.0, max(0.0,
        0.35 * selected.scale_tick_score
        + 0.25 * (1.0 - selected.range_support)
        + 0.20 * min(1.0, (selected.header_distance or 0.03) / 0.03)
        + 0.20 * (1.0 / (1.0 + max(0.0, margin)))
    ))
    return NativeStructuralPrediction(
        status="selected", reason="semantic_depth_column_with_native_bbox_evidence",
        boundaries=tuple(boundaries), selected_columns=(selected,),
        candidates=tuple(candidates[:12]), document_signals=tuple(signals),
        risk_score=risk,
    )
