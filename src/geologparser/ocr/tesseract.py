"""Tesseract CLI adapter used as a transparent CPU smoke-test baseline."""

from __future__ import annotations

import csv
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from .base import OCRBackendUnavailable, TextRegion


class TesseractOCRAdapter:
    name = "tesseract"

    def __init__(self, language: str = "chi_sim+eng", psm: int = 6) -> None:
        self.language = language
        self.psm = psm

    def extract(self, path: Path) -> list[TextRegion]:
        executable = shutil.which("tesseract")
        if executable is None:
            raise OCRBackendUnavailable("The tesseract executable is not installed or not on PATH.")
        command = [executable, str(path), "stdout", "-l", self.language, "--psm", str(self.psm), "tsv"]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise OCRBackendUnavailable(f"Tesseract failed ({completed.returncode}): {completed.stderr.strip()}")
        grouped: dict[tuple[int, int, int, int], list[dict[str, str]]] = defaultdict(list)
        for row in csv.DictReader(completed.stdout.splitlines(), delimiter="\t"):
            text = row.get("text", "").strip()
            if text:
                key = tuple(int(row[name]) for name in ("page_num", "block_num", "par_num", "line_num"))
                grouped[key].append(row)
        regions: list[TextRegion] = []
        for (page, _, _, _), rows in grouped.items():
            left = min(float(row["left"]) for row in rows)
            top = min(float(row["top"]) for row in rows)
            right = max(float(row["left"]) + float(row["width"]) for row in rows)
            bottom = max(float(row["top"]) + float(row["height"]) for row in rows)
            confidences = [float(row["conf"]) / 100.0 for row in rows if float(row["conf"]) >= 0]
            regions.append(TextRegion(
                page=page,
                bbox=(float(left), float(top), float(right), float(bottom)),
                text=" ".join(row["text"].strip() for row in rows),
                confidence=sum(confidences) / len(confidences) if confidences else None,
                method="ocr",
            ))
        return regions
