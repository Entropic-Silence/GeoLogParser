import shutil
import subprocess

import pytest

from geologparser.pdf import PdftotextAdapter
from geologparser.pipeline import run_minimal_baseline


@pytest.mark.skipif(shutil.which("gs") is None or shutil.which("pdftotext") is None, reason="PDF system tools unavailable")
def test_pdftotext_real_smoke(tmp_path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "fixture.pdf"
    postscript.write_text(
        "%!PS-Adobe-3.0\n"
        "<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 18 scalefont setfont\n"
        "72 730 moveto (Borehole ID: ZK-PDF-01) show\n"
        "72 690 moveto (Final Depth: 4.50 m) show\n"
        "showpage\n",
        encoding="ascii",
    )
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)], check=True)
    regions = PdftotextAdapter().extract(pdf)
    assert len(regions) == 1
    assert "ZK-PDF-01" in regions[0].text
    assert regions[0].bbox is None


@pytest.mark.skipif(shutil.which("gs") is None or shutil.which("pdftotext") is None, reason="PDF system tools unavailable")
def test_native_pdf_full_pipeline(tmp_path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "fixture.pdf"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 18 scalefont setfont\n"
        "72 730 moveto (Borehole ID: ZK-PDF-02) show\n"
        "72 690 moveto (Final Depth: 4.50 m) show\n"
        "72 650 moveto (0.00 4.50 4.50 SILT firm) show\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)], check=True)
    regions, record = run_minimal_baseline(pdf)
    assert regions[0].method == "direct_pdf_text"
    assert record["borehole"]["borehole_id"]["value"] == "ZK-PDF-02"
    assert record["borehole"]["final_depth_m"]["value"] == 4.5
    assert len(record["intervals"]) == 1


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("gs", "pdftotext", "pdftoppm", "tesseract")),
    reason="scanned-PDF OCR system tools unavailable",
)
def test_image_only_pdf_uses_ocr_pipeline(tmp_path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "scanned.pdf"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 24 scalefont setfont\n"
        "72 730 moveto (Borehole ID: ZK-SCAN-01) true charpath fill\n"
        "72 680 moveto (Final Depth: 4.50 m) true charpath fill\n"
        "72 630 moveto (0.00 4.50 4.50 SILT firm) true charpath fill\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)], check=True)
    assert not subprocess.run(["pdftotext", str(pdf), "-"], text=True, capture_output=True, check=True).stdout.strip()
    regions, record = run_minimal_baseline(pdf, ocr_language="eng")
    assert any(region.method == "ocr" for region in regions)
    assert record["borehole"]["final_depth_m"]["value"] == 4.5
    assert len(record["intervals"]) == 1
