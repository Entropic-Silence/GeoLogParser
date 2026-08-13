from pathlib import Path

import pytest

from geologparser.cad_raster import (
    RasterAuditConfig, compare_rasters, foreground_mask, normalized_occupancy,
)


def write_image(path: Path, lines=()):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (120, 240), "black")
    draw = ImageDraw.Draw(image)
    for line in lines:
        draw.line(line, fill="white", width=3)
    image.save(path)


def test_foreground_audit_detects_blank_and_content(tmp_path):
    blank, content = tmp_path / "blank.png", tmp_path / "content.png"
    write_image(blank)
    write_image(content, [((20, 10), (20, 230)), ((20, 10), (100, 10))])
    _, blank_audit = foreground_mask(blank)
    _, content_audit = foreground_mask(content)
    assert blank_audit["raster_nonblank"] is False
    assert content_audit["raster_nonblank"] is True
    assert content_audit["foreground_pixels"] > 0
    assert content_audit["content_bbox_pixels"] == [19, 9, 101, 231]


def test_identical_rasters_have_complete_overlap(tmp_path):
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    lines = [((20, 10), (20, 230)), ((20, 10), (100, 10))]
    write_image(first, lines)
    write_image(second, lines)
    result = compare_rasters(first, second)
    assert result["status"] == "compared_overlap_at_or_above_threshold"
    assert result["raw_iou"] == 1
    assert result["tolerant_bidirectional_f1"] == pytest.approx(1)
    assert result["visual_fidelity_status"] == "not_assessed"


def test_different_rasters_are_reported_without_fidelity_claim(tmp_path):
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    write_image(first, [((10, 10), (10, 230))])
    write_image(second, [((110, 10), (110, 230)), ((10, 120), (110, 120))])
    result = compare_rasters(
        first, second, config=RasterAuditConfig(minimum_tolerant_f1=0.9),
    )
    assert result["status"] == "compared_overlap_below_threshold"
    assert result["tolerant_bidirectional_f1"] < 0.9
    assert "not visual fidelity" not in result["status"]


def test_placeholder_is_never_compared(tmp_path):
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    write_image(first, [((10, 10), (10, 230))])
    write_image(second, [((10, 10), (10, 230))])
    result = compare_rasters(first, second, second_is_placeholder=True)
    assert result["status"] == "not_comparable_placeholder"
    assert result["raw_iou"] is None


def test_downsampling_preserves_one_pixel_cad_lines(tmp_path):
    from PIL import Image, ImageDraw

    image = Image.new("L", (1000, 4000), 0)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 999, 3999), outline=255, width=1)
    occupancy = normalized_occupancy(image, 256, 1024)
    bbox = occupancy.getbbox()
    assert bbox is not None
    assert bbox[0] == 0 and bbox[1] == 0
    assert bbox[2] == 256 and bbox[3] == 1024


def test_config_rejects_invalid_thresholds():
    with pytest.raises(ValueError, match="minimum_tolerant_f1"):
        RasterAuditConfig(minimum_tolerant_f1=1.1)
