from pathlib import Path

import pytest
from PIL import Image

from geologparser.preprocessing import DegradationConfig, degrade_image


def test_degradation_is_seeded_and_records_hashes(tmp_path: Path):
    source = tmp_path / "source.png"
    Image.new("RGB", (20, 10), "gray").save(source)
    config = DegradationConfig(blur_radius=1, gaussian_noise_std=4, contrast=.8, seed=7)
    first = degrade_image(source, tmp_path / "first.png", config)
    second = degrade_image(source, tmp_path / "second.png", config)
    assert first["destination_sha256"] == second["destination_sha256"]
    assert first["parameters"]["seed"] == 7
    assert (first["width"], first["height"]) == (20, 10)


def test_extended_degradations_are_seeded_and_record_all_parameters(tmp_path: Path):
    source = tmp_path / "source.png"
    Image.new("RGB", (240, 160), "gray").save(source)
    config = DegradationConfig(
        resolution_scale=.5, broken_line_count=3, watermark_text="AUDIT",
        stamp_count=1, occlusion_fraction=.05, seed=9,
    )
    first = degrade_image(source, tmp_path / "first.jpg", config)
    second = degrade_image(source, tmp_path / "second.jpg", config)
    assert first["destination_sha256"] == second["destination_sha256"]
    assert first["parameters"]["resolution_scale"] == .5
    assert first["parameters"]["broken_line_count"] == 3
    assert first["parameters"]["watermark_text"] == "AUDIT"
    assert "partial_occlusion" in first["operation_order"]


def test_degradation_validates_jpeg_quality(tmp_path: Path):
    source = tmp_path / "source.png"
    Image.new("RGB", (10, 10), "white").save(source)
    with pytest.raises(ValueError):
        degrade_image(source, tmp_path / "bad.jpg", DegradationConfig(jpeg_quality=101))
    with pytest.raises(ValueError):
        degrade_image(source, tmp_path / "bad2.jpg", DegradationConfig(resolution_scale=0))
    with pytest.raises(ValueError):
        degrade_image(source, tmp_path / "bad3.jpg", DegradationConfig(occlusion_fraction=.8))
