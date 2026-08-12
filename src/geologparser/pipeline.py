"""Minimal, explicit baseline orchestration."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from geologparser.extraction import extract_structured
from geologparser.ocr import OCRBackendUnavailable, TesseractOCRAdapter, TextRegion
from geologparser.pdf import PdftotextAdapter, PyMuPDFTextAdapter


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def extract_text_regions(path: Path, ocr_language: str = "chi_sim+eng") -> list[TextRegion]:
    extension = path.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        return TesseractOCRAdapter(language=ocr_language).extract(path)
    if extension == ".pdf":
        try:
            direct = PyMuPDFTextAdapter().extract(path)
        except OCRBackendUnavailable:
            direct = PdftotextAdapter().extract(path)
        if any(region.text.strip() for region in direct):
            return direct
        renderer = shutil.which("pdftoppm")
        if renderer is None:
            raise OCRBackendUnavailable("Scanned-PDF OCR requires pdftoppm (Poppler).")
        with tempfile.TemporaryDirectory(prefix="geologparser-pdf-") as temporary:
            prefix = Path(temporary) / "page"
            completed = subprocess.run(
                [renderer, "-png", "-r", "300", str(path), str(prefix)],
                text=True, capture_output=True, check=False,
            )
            if completed.returncode != 0:
                raise OCRBackendUnavailable(f"pdftoppm failed ({completed.returncode}): {completed.stderr.strip()}")
            page_paths = sorted(Path(temporary).glob("page-*.png"))
            if not page_paths:
                raise OCRBackendUnavailable("pdftoppm emitted no page images")
            regions = []
            adapter = TesseractOCRAdapter(language=ocr_language)
            for page_number, page_path in enumerate(page_paths, start=1):
                regions.extend(replace(region, page=page_number) for region in adapter.extract(page_path))
            return regions
    if extension == ".txt":
        return [TextRegion(page=1, bbox=None, text=path.read_text(encoding="utf-8"), confidence=None, method="unknown")]
    raise ValueError(f"Unsupported input extension: {extension}")


def run_minimal_baseline(path: Path, ocr_language: str = "chi_sim+eng") -> tuple[list[TextRegion], dict]:
    regions = extract_text_regions(path, ocr_language=ocr_language)
    return regions, extract_structured(regions, path)
