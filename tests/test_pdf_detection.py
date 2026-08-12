from geologparser.pdf import detection
from geologparser.pdf.detection import PDFDetectionConfig, detect_pdf


def test_sparse_header_over_large_scan_is_scanned(monkeypatch, tmp_path):
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-fixture")
    monkeypatch.setattr(detection.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(detection, "_page_count", lambda path: 1)
    monkeypatch.setattr(detection, "_text_characters", lambda path, page: 57)
    monkeypatch.setattr(detection, "_largest_image_pixels", lambda path, page: 8_000_000)
    result = detect_pdf(source)
    assert result.document_type == "scanned_pdf"
    assert result.pages[0].reason == "large_image_with_sparse_text"


def test_native_and_scanned_pages_form_mixed_pdf(monkeypatch, tmp_path):
    source = tmp_path / "mixed.pdf"
    source.write_bytes(b"%PDF-fixture")
    monkeypatch.setattr(detection.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(detection, "_page_count", lambda path: 2)
    monkeypatch.setattr(detection, "_text_characters", lambda path, page: {1: 600, 2: 0}[page])
    monkeypatch.setattr(detection, "_largest_image_pixels", lambda path, page: {1: 0, 2: 5_000_000}[page])
    result = detect_pdf(source, PDFDetectionConfig(minimum_native_characters=300))
    assert result.document_type == "mixed_pdf"
    assert [page.classification for page in result.pages] == ["native", "scanned"]

