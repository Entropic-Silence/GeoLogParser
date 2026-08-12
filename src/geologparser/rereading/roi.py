"""High-resolution ROI crop and numeric OCR candidate generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from geologparser.ocr import OCRAdapter, TextRegion

from .core import Candidate


NUMERIC_CANDIDATE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


@dataclass(frozen=True)
class ROICrop:
    source_path: str
    bbox_pixels: tuple[int, int, int, int]
    scale: float
    output_path: str


def crop_roi(
    source_path: Path,
    bbox_pixels: Sequence[float],
    output_path: Path,
    padding_pixels: int = 8,
    scale: float = 2.0,
) -> ROICrop:
    if len(bbox_pixels) != 4:
        raise ValueError("bbox must have four coordinates")
    if padding_pixels < 0 or scale <= 0:
        raise ValueError("padding must be non-negative and scale positive")
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("ROI crop requires Pillow") from exc
    with Image.open(source_path) as image:
        x1, y1, x2, y2 = bbox_pixels
        left = max(0, int(x1) - padding_pixels)
        top = max(0, int(y1) - padding_pixels)
        right = min(image.width, int(x2 + 0.9999) + padding_pixels)
        bottom = min(image.height, int(y2 + 0.9999) + padding_pixels)
        if right <= left or bottom <= top:
            raise ValueError("bbox is empty after clamping")
        crop = image.crop((left, top, right, bottom))
        if scale != 1:
            crop = crop.resize(
                (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
                Image.Resampling.LANCZOS,
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(output_path)
    return ROICrop(str(source_path), (left, top, right, bottom), scale, str(output_path))


def numeric_candidates_from_regions(
    regions: Sequence[TextRegion],
    source: str,
) -> list[Candidate]:
    candidates: dict[str, Candidate] = {}
    for region in regions:
        for match in NUMERIC_CANDIDATE.finditer(region.text):
            raw = match.group(0)
            normalized = raw.replace(",", ".")
            value = float(normalized)
            key = normalized
            candidate = Candidate(
                value=value, source=source, source_text=raw,
                model_confidence=region.confidence,
                pixel_evidence=region.confidence,
                layout_confidence=1.0,
            )
            existing = candidates.get(key)
            if existing is None or (candidate.model_confidence or 0) > (existing.model_confidence or 0):
                candidates[key] = candidate
    return list(candidates.values())


def reread_numeric_roi(
    source_path: Path,
    bbox_pixels: Sequence[float],
    output_path: Path,
    adapters: Sequence[OCRAdapter],
    padding_pixels: int = 8,
    scale: float = 2.0,
) -> tuple[ROICrop, list[Candidate], dict[str, list[TextRegion]]]:
    crop = crop_roi(source_path, bbox_pixels, output_path, padding_pixels, scale)
    all_candidates: list[Candidate] = []
    outputs: dict[str, list[TextRegion]] = {}
    for adapter in adapters:
        regions = adapter.extract(Path(crop.output_path))
        outputs[adapter.name] = regions
        all_candidates.extend(numeric_candidates_from_regions(regions, adapter.name))
    return crop, all_candidates, outputs
