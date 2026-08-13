import json
import shutil
import subprocess
from pathlib import Path

import pytest

from geologparser.annotation import (
    PanelSpec, create_annotation, human_empty_interval, matching_attestations,
    pdf_bbox_to_rendered_pixels, render_panel, revise_annotation, save_annotation,
    validate_display_bbox,
)


ROOT = Path(__file__).resolve().parents[1]


def sample_record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_panel_spec_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        PanelSpec("x", "/tmp/x.pdf", 1, (0.5, 0, 0.4, 1)).validate()


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_display_bbox_rejects_nonfinite_coordinates(value):
    with pytest.raises(ValueError, match="finite"):
        validate_display_bbox([0, 0, value, 10], {"rendered_width_px": 200, "rendered_height_px": 100})


def test_human_empty_interval_is_schema_ready_without_invented_values():
    interval = human_empty_interval("I001", 3)
    assert interval["interval_id"] == "I001"
    for name, envelope in interval.items():
        if name == "interval_id":
            continue
        assert envelope["value"] is None
        assert envelope["source_page"] == 3
        assert envelope["extraction_method"] == "human"
        assert envelope["validation_status"] == "not_validated"


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


def test_legacy_auto_annotation_without_attestation_key_remains_valid():
    annotation = create_annotation("a1", {"panel_id": "p1"}, sample_record(), "AUTO")
    annotation.pop("verification_attestations")
    from geologparser.annotation import validate_annotation
    validate_annotation(annotation)


def test_single_verification_attestation_is_bound_to_exact_record():
    source = sample_record()
    first = create_annotation("a1", {"panel_id": "p1"}, source, "reviewer-1", "single_verified")
    assert [item["annotator_id"] for item in matching_attestations(first)] == ["reviewer-1"]
    source["borehole"]["borehole_id"]["value"] = "CALLER_MUTATION"
    assert first["record"]["borehole"]["borehole_id"]["value"] != "CALLER_MUTATION"
    first["record"]["borehole"]["borehole_id"]["value"] = "CHANGED"
    assert matching_attestations(first) == []


def test_double_verification_requires_two_people_on_identical_record():
    first = create_annotation(
        "a1", {"panel_id": "p1"}, sample_record(), "reviewer-1", "single_verified",
    )
    second = revise_annotation(first, first["record"], "reviewer-2", "double_verified")
    assert second["annotation_status"] == "double_verified"
    assert {item["annotator_id"] for item in matching_attestations(second)} == {
        "reviewer-1", "reviewer-2",
    }

    changed = sample_record()
    changed["borehole"]["borehole_id"]["value"] = "CHANGED"
    with pytest.raises(ValueError, match="two distinct annotators"):
        revise_annotation(first, changed, "reviewer-2", "double_verified")
    with pytest.raises(ValueError, match="two distinct annotators"):
        revise_annotation(first, first["record"], "reviewer-1", "double_verified")


def test_expert_verification_requires_expert_role():
    first = create_annotation("a1", {"panel_id": "p1"}, sample_record(), "AUTO", "auto")
    with pytest.raises(ValueError, match="configured expert"):
        revise_annotation(first, first["record"], "reviewer-1", "expert_verified")
    expert = revise_annotation(
        first, first["record"], "expert-1", "expert_verified", actor_role="expert",
    )
    assert matching_attestations(expert)[0]["role"] == "expert"


@pytest.mark.parametrize("status", ["double_verified", "expert_verified"])
def test_high_assurance_status_cannot_be_claimed_at_creation(status):
    with pytest.raises(ValueError, match="single annotation creation"):
        create_annotation("a1", {"panel_id": "p1"}, sample_record(), "reviewer-1", status)


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
