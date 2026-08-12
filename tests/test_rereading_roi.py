import shutil
import subprocess
from pathlib import Path

import pytest

from geologparser.ocr import TesseractOCRAdapter, TextRegion
from geologparser.rereading import crop_roi, numeric_candidates_from_regions, reread_numeric_roi


class FakeAdapter:
    name = "fake_vlm"

    def extract(self, _path):
        return [TextRegion(1, (0, 0, 10, 10), "4.50 / alt 4,80", 0.9, "ocr")]


def test_crop_roi_clamps_padding_and_scales(tmp_path: Path):
    from PIL import Image
    source = tmp_path / "source.png"
    output = tmp_path / "roi.png"
    Image.new("RGB", (100, 80), "white").save(source)
    crop = crop_roi(source, (2, 3, 20, 13), output, padding_pixels=8, scale=2)
    assert crop.bbox_pixels == (0, 0, 28, 21)
    assert Image.open(output).size == (56, 42)


def test_numeric_candidate_parser_preserves_raw_decimal_separator():
    candidates = numeric_candidates_from_regions(
        [TextRegion(1, None, "value 4,80 and 4.50", 0.8, "ocr")], "fake",
    )
    assert [(candidate.value, candidate.source_text) for candidate in candidates] == [(4.8, "4,80"), (4.5, "4.50")]


def test_reread_numeric_roi_runs_adapter_on_crop(tmp_path: Path):
    from PIL import Image
    source = tmp_path / "source.png"
    Image.new("RGB", (100, 80), "white").save(source)
    crop, candidates, outputs = reread_numeric_roi(
        source, (10, 10, 40, 30), tmp_path / "roi.png", [FakeAdapter()], scale=1,
    )
    assert Path(crop.output_path).is_file()
    assert {candidate.value for candidate in candidates} == {4.5, 4.8}
    assert len(outputs["fake_vlm"]) == 1


@pytest.mark.skipif(
    shutil.which("gs") is None or shutil.which("tesseract") is None,
    reason="real OCR fixture tools unavailable",
)
def test_real_tesseract_roi_reread(tmp_path: Path):
    postscript = tmp_path / "fixture.ps"
    source = tmp_path / "source.png"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [300 120] >> setpagedevice\n"
        "/Courier-Bold findfont 42 scalefont setfont\n40 45 moveto (4.50) show\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pnggray", "-r150", f"-sOutputFile={source}", str(postscript)],
        check=True,
    )
    from PIL import Image
    width, height = Image.open(source).size
    _, candidates, _ = reread_numeric_roi(
        source, (0, 0, width, height), tmp_path / "roi.png",
        [TesseractOCRAdapter(language="eng", psm=6)], padding_pixels=0, scale=2,
    )
    assert any(candidate.value == pytest.approx(4.5) for candidate in candidates)
