"""Common OCR output and adapter protocol."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TextRegion:
    page: int
    bbox: tuple[float, float, float, float] | None
    text: str
    confidence: float | None
    method: str


class OCRAdapter(Protocol):
    name: str

    def extract(self, path: Path) -> list[TextRegion]: ...


class OCRBackendUnavailable(RuntimeError):
    pass

