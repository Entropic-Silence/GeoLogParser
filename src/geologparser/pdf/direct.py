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
        return self.extract_pages(path, None)

    def extract_pages(self, path: Path, pages: set[int] | None) -> list[TextRegion]:
        import shutil
        import subprocess

        executable = shutil.which("pdftotext")
        if executable is None:
            raise OCRBackendUnavailable("The pdftotext executable is not installed or not on PATH.")
        regions = []
        page_numbers = sorted(pages) if pages is not None else [None]
        for requested_page in page_numbers:
            page_args = [] if requested_page is None else ["-f", str(requested_page), "-l", str(requested_page)]
            completed = subprocess.run(
                [executable, *page_args, "-layout", str(path), "-"],
                text=True, capture_output=True, check=False,
            )
            if completed.returncode != 0:
                raise OCRBackendUnavailable(f"pdftotext failed ({completed.returncode}): {completed.stderr.strip()}")
            extracted_pages = completed.stdout.split("\f")
            for offset, page_text in enumerate(extracted_pages):
                if not page_text.strip():
                    continue
                page_number = requested_page if requested_page is not None else offset + 1
                regions.append(TextRegion(
                    page=page_number, bbox=None, text=page_text.strip(), confidence=None,
                    method="direct_pdf_text",
                ))
        return regions
