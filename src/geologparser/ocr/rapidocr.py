"""Optional CPU RapidOCR/ONNX Runtime adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import OCRBackendUnavailable, TextRegion


DEFAULT_MODEL_DIR = Path("/data/GeoLogParser/models/rapidocr")
MODEL_FILENAMES = {
    "det_model_path": "ch_PP-OCRv4_det_infer.onnx",
    "rec_model_path": "ch_PP-OCRv4_rec_infer.onnx",
    "cls_model_path": "ch_ppocr_mobile_v2.0_cls_infer.onnx",
}


class RapidOCROnnxAdapter:
    name = "rapidocr_onnxruntime"

    def __init__(self, model_dir: Path = DEFAULT_MODEL_DIR, intra_op_num_threads: int = 4) -> None:
        self.model_dir = Path(model_dir)
        self.intra_op_num_threads = intra_op_num_threads
        self._engine: Any = None

    def _build_engine(self):
        missing = [name for name in MODEL_FILENAMES.values() if not (self.model_dir / name).is_file()]
        if missing:
            raise OCRBackendUnavailable(
                f"RapidOCR model directory {self.model_dir} is missing: {', '.join(missing)}"
            )
        try:
            from rapidocr_onnxruntime import RapidOCR
        except (ImportError, OSError) as exc:
            raise OCRBackendUnavailable(
                "rapidocr_onnxruntime is unavailable; install the versioned optional OCR requirements"
            ) from exc
        paths = {key: str(self.model_dir / filename) for key, filename in MODEL_FILENAMES.items()}
        return RapidOCR(
            **paths,
            intra_op_num_threads=self.intra_op_num_threads,
            inter_op_num_threads=1,
            det_use_cuda=False,
            cls_use_cuda=False,
            rec_use_cuda=False,
        )

    def extract(self, path: Path) -> list[TextRegion]:
        if not path.is_file():
            raise OCRBackendUnavailable(f"OCR image does not exist: {path}")
        if self._engine is None:
            self._engine = self._build_engine()
        try:
            result, _elapsed = self._engine(path)
        except Exception as exc:
            raise OCRBackendUnavailable(f"RapidOCR failed for {path}: {exc}") from exc
        regions: list[TextRegion] = []
        for item in result or ():
            if len(item) < 3:
                continue
            polygon, text, confidence = item[:3]
            x_values = [float(point[0]) for point in polygon]
            y_values = [float(point[1]) for point in polygon]
            regions.append(TextRegion(
                page=1,
                bbox=(min(x_values), min(y_values), max(x_values), max(y_values)),
                text=str(text),
                confidence=float(confidence),
                method="ocr",
            ))
        return regions
