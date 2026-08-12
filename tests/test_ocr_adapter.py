import shutil
import subprocess

import pytest

from geologparser.ocr import TesseractOCRAdapter


@pytest.mark.skipif(shutil.which("tesseract") is None or shutil.which("gs") is None, reason="OCR system tools unavailable")
def test_tesseract_cli_adapter_real_smoke(tmp_path):
    postscript = tmp_path / "fixture.ps"
    image = tmp_path / "fixture.png"
    postscript.write_text(
        "%!PS-Adobe-3.0\n"
        "<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 26 scalefont setfont\n"
        "72 730 moveto (Borehole ID: ZK-01) show\n"
        "72 680 moveto (Final Depth: 4.50 m) show\n"
        "72 630 moveto (0.00 1.20 1.20 FILL loose) show\n"
        "72 580 moveto (1.20 4.50 3.30 SILTY_CLAY plastic) show\n"
        "showpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pnggray", "-r300", f"-sOutputFile={image}", str(postscript)],
        check=True,
    )
    regions = TesseractOCRAdapter(language="eng", psm=6).extract(image)
    text = " ".join(region.text for region in regions)
    assert "Borehole" in text
    assert "4.50" in text
    assert all(region.bbox is not None for region in regions)
