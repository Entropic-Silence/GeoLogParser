from pathlib import Path

import pytest

from geologparser.ocr import OCRBackendUnavailable, RapidOCROnnxAdapter


class FakeRapidOCR:
    def __call__(self, _path):
        return [
            [[[10, 20], [100, 18], [101, 40], [9, 42]], "终孔深度 4.50m", 0.93],
        ], [0.1, 0.2, 0.3]


def test_rapidocr_adapter_maps_polygon_to_common_region(tmp_path: Path):
    image = tmp_path / "fixture.png"
    image.write_bytes(b"not decoded by fake")
    adapter = RapidOCROnnxAdapter(model_dir=tmp_path)
    adapter._engine = FakeRapidOCR()
    regions = adapter.extract(image)
    assert regions[0].bbox == (9.0, 18.0, 101.0, 42.0)
    assert regions[0].text == "终孔深度 4.50m"
    assert regions[0].confidence == pytest.approx(0.93)
    assert regions[0].method == "ocr"


def test_rapidocr_adapter_reports_missing_models(tmp_path: Path):
    with pytest.raises(OCRBackendUnavailable, match="missing"):
        RapidOCROnnxAdapter(model_dir=tmp_path)._build_engine()


@pytest.mark.skipif(
    not Path("/data/GeoLogParser/models/rapidocr/ch_PP-OCRv4_det_infer.onnx").is_file(),
    reason="versioned RapidOCR model assets unavailable",
)
def test_rapidocr_real_engine_smoke(tmp_path: Path):
    try:
        import cv2
        import numpy as np
    except ImportError:
        pytest.skip("RapidOCR runtime unavailable")
    image = np.full((180, 900, 3), 255, dtype=np.uint8)
    cv2.putText(image, "Borehole ZK-01 Depth 4.50m", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    path = tmp_path / "rapidocr.png"
    assert cv2.imwrite(str(path), image)
    regions = RapidOCROnnxAdapter(intra_op_num_threads=2).extract(path)
    assert regions
    assert any("4.50" in region.text for region in regions)
    assert all(region.bbox is not None for region in regions)
