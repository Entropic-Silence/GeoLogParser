"""Minimal, explicit baseline orchestration."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path

from geologparser.extraction import extract_structured
from geologparser.ocr import OCRAdapter, OCRBackendUnavailable, TesseractOCRAdapter, TextRegion
from geologparser.pdf import PdftotextAdapter, detect_pdf


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def extract_text_regions(
    path: Path,
    ocr_language: str = "chi_sim+eng",
    ocr_adapter: OCRAdapter | None = None,
    render_dpi: int = 300,
) -> list[TextRegion]:
    adapter = ocr_adapter or TesseractOCRAdapter(language=ocr_language)
    extension = path.suffix.lower()
    if extension in IMAGE_EXTENSIONS:
        return adapter.extract(path)
    if extension == ".pdf":
        detection = detect_pdf(path)
        native_pages = {page.page for page in detection.pages if page.classification == "native"}
        scanned_pages = {page.page for page in detection.pages if page.classification == "scanned"}
        regions = PdftotextAdapter().extract_pages(path, native_pages) if native_pages else []
        if not scanned_pages:
            return regions
        renderer = shutil.which("pdftoppm")
        if renderer is None:
            raise OCRBackendUnavailable("Scanned-PDF OCR requires pdftoppm (Poppler).")
        with tempfile.TemporaryDirectory(prefix="geologparser-pdf-") as temporary:
            prefix = Path(temporary) / "page"
            for page_number in sorted(scanned_pages):
                completed = subprocess.run(
                    [renderer, "-f", str(page_number), "-l", str(page_number), "-singlefile", "-png", "-r", str(render_dpi), str(path), str(prefix)],
                    text=True, capture_output=True, check=False,
                )
                if completed.returncode != 0:
                    raise OCRBackendUnavailable(f"pdftoppm failed ({completed.returncode}): {completed.stderr.strip()}")
                page_path = prefix.with_suffix(".png")
                if not page_path.exists():
                    raise OCRBackendUnavailable("pdftoppm emitted no page image")
                regions.extend(replace(region, page=page_number) for region in adapter.extract(page_path))
                page_path.unlink()
            return regions
    if extension == ".txt":
        return [TextRegion(page=1, bbox=None, text=path.read_text(encoding="utf-8"), confidence=None, method="unknown")]
    raise ValueError(f"Unsupported input extension: {extension}")


def run_minimal_baseline(
    path: Path,
    ocr_language: str = "chi_sim+eng",
    ocr_adapter: OCRAdapter | None = None,
    render_dpi: int = 300,
) -> tuple[list[TextRegion], dict]:
    regions = extract_text_regions(
        path, ocr_language=ocr_language, ocr_adapter=ocr_adapter, render_dpi=render_dpi,
    )
    return regions, extract_structured(regions, path)
