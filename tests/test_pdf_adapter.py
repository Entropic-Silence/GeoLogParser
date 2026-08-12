import shutil
import subprocess
from pathlib import Path

import pytest

from geologparser.pdf import PdftotextAdapter, PyMuPDFPanelTextAdapter
from geologparser.ocr import TextRegion
from geologparser.pipeline import run_minimal_baseline


class RecordingOCRAdapter:
    name = "recording"

    def __init__(self):
        self.paths: list[Path] = []

    def extract(self, path: Path) -> list[TextRegion]:
        self.paths.append(path)
        return [TextRegion(
            page=1, bbox=(0, 0, 100, 20), confidence=0.9, method="ocr",
            text="Borehole ID: INJECTED-01 Final Depth: 2.00 m",
        )]


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


@pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in ("gs", "pdftotext", "pdftoppm")),
    reason="scanned-PDF rendering tools unavailable",
)
def test_scanned_pdf_uses_injected_ocr_adapter(tmp_path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "scanned.pdf"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 24 scalefont setfont\n"
        "72 730 moveto (raster outlines only) true charpath fill\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)],
        check=True,
    )
    adapter = RecordingOCRAdapter()
    regions, record = run_minimal_baseline(pdf, ocr_adapter=adapter, render_dpi=144)
    assert len(adapter.paths) == 1
    assert regions[0].page == 1
    assert record["borehole"]["borehole_id"]["value"] == "INJECTED-01"


@pytest.mark.skipif(shutil.which("gs") is None, reason="PDF fixture tool unavailable")
def test_panel_text_adapter_separates_visual_halves_on_rotated_page(tmp_path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "fixture.pdf"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [842 595] >> setpagedevice\n"
        "/Courier findfont 20 scalefont setfont\n"
        "72 500 moveto (LEFT_BOREHOLE) show\n"
        "500 500 moveto (RIGHT_BOREHOLE) show\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)],
        check=True,
    )
    adapter = PyMuPDFPanelTextAdapter()
    left = " ".join(region.text for region in adapter.extract_panel(pdf, 1, (0, 0, 0.5, 1)))
    right = " ".join(region.text for region in adapter.extract_panel(pdf, 1, (0.5, 0, 1, 1)))
    assert "LEFT_BOREHOLE" in left and "RIGHT_BOREHOLE" not in left
    assert "RIGHT_BOREHOLE" in right and "LEFT_BOREHOLE" not in right
