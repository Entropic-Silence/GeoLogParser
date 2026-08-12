"""Native PDF text extraction adapter."""

from __future__ import annotations

from pathlib import Path

from geologparser.ocr.base import OCRBackendUnavailable, TextRegion


class PyMuPDFTextAdapter:
    name = "pymupdf_direct_text"

    def extract(self, path: Path) -> list[TextRegion]:
        try:
            import fitz
        except ImportError as exc:
            raise OCRBackendUnavailable(
                "Native PDF extraction requires PyMuPDF; install geologparser[pdf]."
            ) from exc
        regions: list[TextRegion] = []
        with fitz.open(path) as document:
            for page_index, page in enumerate(document):
                for block in page.get_text("blocks"):
                    text = str(block[4]).strip()
                    if text:
                        regions.append(TextRegion(
                            page=page_index + 1,
                            bbox=(float(block[0]), float(block[1]), float(block[2]), float(block[3])),
                            text=text,
                            confidence=None,
                            method="direct_pdf_text",
                        ))
        return regions


class PdftotextAdapter:
    """Dependency-light fallback; bbox is unavailable and remains explicitly null."""

    name = "pdftotext_direct_text"

    def extract(self, path: Path) -> list[TextRegion]:
        import shutil
        import subprocess

        executable = shutil.which("pdftotext")
        if executable is None:
            raise OCRBackendUnavailable("The pdftotext executable is not installed or not on PATH.")
        completed = subprocess.run(
            [executable, "-layout", str(path), "-"],
            text=True, capture_output=True, check=False,
        )
        if completed.returncode != 0:
            raise OCRBackendUnavailable(f"pdftotext failed ({completed.returncode}): {completed.stderr.strip()}")
        regions = []
        for page_number, page_text in enumerate(completed.stdout.split("\f"), start=1):
            if page_text.strip():
                regions.append(TextRegion(
                    page=page_number, bbox=None, text=page_text.strip(), confidence=None,
                    method="direct_pdf_text",
                ))
        return regions
