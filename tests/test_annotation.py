import json
import shutil
import subprocess
from pathlib import Path

import pytest

from geologparser.annotation import (
    PanelSpec, create_annotation, pdf_bbox_to_rendered_pixels, render_panel,
    revise_annotation, save_annotation,
)


ROOT = Path(__file__).resolve().parents[1]


def sample_record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_panel_spec_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        PanelSpec("x", "/tmp/x.pdf", 1, (0.5, 0, 0.4, 1)).validate()


def test_revisioned_annotation_preserves_history(tmp_path: Path):
    panel = {"panel_id": "p1", "source_sha256": "a" * 64}
    first = create_annotation("a1", panel, sample_record(), "annotator-A", "single_verified")
    destination = tmp_path / "a1.json"
    save_annotation(first, destination)
    record = sample_record()
    record["borehole"]["borehole_id"]["value"] = "CORRECTED"
    second = revise_annotation(first, record, "annotator-A", "single_verified")
    save_annotation(second, destination)
    assert json.loads(destination.read_text())["revision"] == 2
    history = tmp_path / "history/a1/revision_0001.json"
    assert json.loads(history.read_text())["revision"] == 1


def test_revision_conflict_is_rejected(tmp_path: Path):
    first = create_annotation("a1", {"panel_id": "p1"}, sample_record(), "A")
    destination = tmp_path / "a1.json"
    save_annotation(first, destination)
    with pytest.raises(ValueError, match="revision conflict"):
        save_annotation(first, destination)


def test_pdf_bbox_to_rendered_pixels_handles_identity_transform():
    panel = {
        "source_pdf_rotation_matrix": [1, 0, 0, 1, 0, 0],
        "visual_clip_points": [50, 100, 250, 500],
        "rendered_width_px": 400,
        "rendered_height_px": 800,
    }
    assert pdf_bbox_to_rendered_pixels([60, 120, 160, 220], panel) == [20, 40, 220, 240]


def test_pdf_bbox_to_rendered_pixels_handles_90_degree_rotation():
    panel = {
        "source_pdf_rotation_matrix": [0, 1, -1, 0, 1191, 0],
        "visual_clip_points": [0, 0, 595.5, 842],
        "rendered_width_px": 1191,
        "rendered_height_px": 1684,
    }
    result = pdf_bbox_to_rendered_pixels([76.4, 1008.3, 86.9, 1098.5], panel)
    assert result == pytest.approx([185.0, 152.8, 365.4, 173.8])


@pytest.mark.skipif(shutil.which("gs") is None, reason="PDF fixture tool unavailable")
def test_render_panel_freezes_transform_metadata_before_document_closes(tmp_path: Path):
    postscript = tmp_path / "fixture.ps"
    pdf = tmp_path / "fixture.pdf"
    image = tmp_path / "panel.png"
    postscript.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [842 595] >> setpagedevice\n"
        "/Courier findfont 20 scalefont setfont\n72 500 moveto (PANEL) show\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", f"-sOutputFile={pdf}", str(postscript)],
        check=True,
    )
    metadata = render_panel(PanelSpec("p", str(pdf), 1, (0, 0, 0.5, 1)), image, 72)
    assert image.is_file()
    assert len(metadata["source_pdf_rotation_matrix"]) == 6
    assert metadata["visual_clip_points"] == pytest.approx([0, 0, 421, 595])
