"""Native PDF text extraction adapter."""

from __future__ import annotations

from pathlib import Path

from geologparser.ocr.base import OCRBackendUnavailable, TextRegion


class PyMuPDFPanelTextAdapter:
    """Extract positioned native text from a normalized visual-page panel."""

    name = "pymupdf_panel_direct_text"

    def extract_panel(
        self,
        path: Path,
        page_number: int,
        normalized_bbox: tuple[float, float, float, float],
    ) -> list[TextRegion]:
        try:
            import pymupdf
        except ImportError as exc:
            raise OCRBackendUnavailable(
                "Native panel extraction requires PyMuPDF; install geologparser[pdf]."
            ) from exc
        x1, y1, x2, y2 = normalized_bbox
        if page_number < 1:
            raise ValueError("page_number must be one-based")
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise ValueError("normalized_bbox must satisfy 0 <= x1 < x2 <= 1")
        regions: list[TextRegion] = []
        with pymupdf.open(path) as document:
            if page_number > len(document):
                raise ValueError(f"page {page_number} exceeds document page count {len(document)}")
            page = document[page_number - 1]
            visual = page.rect
            visual_clip = pymupdf.Rect(
                visual.x0 + visual.width * x1,
                visual.y0 + visual.height * y1,
                visual.x0 + visual.width * x2,
                visual.y0 + visual.height * y2,
            )
            # Text blocks use the unrotated PDF coordinate system. Convert the
            # user-visible crop before querying, then retain block PDF points as
            # original-source provenance.
            page_clip = visual_clip * page.derotation_matrix
            for block in page.get_text("blocks", clip=page_clip, sort=True):
                text = str(block[4]).strip()
                if text:
                    regions.append(TextRegion(
                        page=page_number,
                        bbox=(float(block[0]), float(block[1]), float(block[2]), float(block[3])),
                        text=text,
                        confidence=None,
                        method="direct_pdf_text",
                    ))
        return regions


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
