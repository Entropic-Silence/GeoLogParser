"""Evidence-based PDF page type detection using Poppler metadata.

The detector intentionally treats a small header text layer over a full-page
scan as scanned content. Thresholds are configuration, not hidden constants in
the extraction pipeline.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from geologparser.ocr.base import OCRBackendUnavailable


@dataclass(frozen=True)
class PDFDetectionConfig:
    minimum_native_characters: int = 300
    large_image_pixels: int = 1_000_000


@dataclass(frozen=True)
class PDFPageEvidence:
    page: int
    text_characters: int
    largest_image_pixels: int
    classification: str
    reason: str


@dataclass(frozen=True)
class PDFDetectionResult:
    document_type: str
    pages: tuple[PDFPageEvidence, ...]


def _run(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise OCRBackendUnavailable(f"{' '.join(command[:1])} failed: {completed.stderr.strip()}")
    return completed.stdout


def _page_count(path: Path) -> int:
    output = _run(["pdfinfo", str(path)])
    match = re.search(r"^Pages:\s+(\d+)$", output, re.MULTILINE)
    if not match:
        raise OCRBackendUnavailable("pdfinfo did not report a page count")
    return int(match.group(1))


def _text_characters(path: Path, page: int) -> int:
    output = _run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(path), "-"])
    return len(re.sub(r"\s+", "", output))


def _largest_image_pixels(path: Path, page: int) -> int:
    output = _run(["pdfimages", "-f", str(page), "-l", str(page), "-list", str(path)])
    largest = 0
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 5 or not all(parts[index].isdigit() for index in (0, 1, 3, 4)):
            continue
        try:
            largest = max(largest, int(parts[3]) * int(parts[4]))
        except (ValueError, IndexError):
            continue
    return largest


def detect_pdf(path: Path, config: PDFDetectionConfig | None = None) -> PDFDetectionResult:
    for executable in ("pdfinfo", "pdftotext", "pdfimages"):
        if shutil.which(executable) is None:
            raise OCRBackendUnavailable(f"PDF detection requires {executable} (Poppler)")
    config = config or PDFDetectionConfig()
    pages = []
    for page in range(1, _page_count(path) + 1):
        characters = _text_characters(path, page)
        image_pixels = _largest_image_pixels(path, page)
        if characters >= config.minimum_native_characters:
            classification = "native"
            reason = "text_above_threshold"
        elif image_pixels >= config.large_image_pixels:
            classification = "scanned"
            reason = "large_image_with_sparse_text"
        elif characters > 0:
            classification = "native"
            reason = "sparse_text_without_large_scan"
        else:
            classification = "scanned"
            reason = "no_text_layer"
        pages.append(PDFPageEvidence(page, characters, image_pixels, classification, reason))
    kinds = {page.classification for page in pages}
    document_type = "mixed_pdf" if len(kinds) > 1 else ("native_pdf" if kinds == {"native"} else "scanned_pdf")
    return PDFDetectionResult(document_type, tuple(pages))
