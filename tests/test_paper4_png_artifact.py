from __future__ import annotations

from PIL import Image

from papers.paper4.build_vector_artwork import save_canonical_raster


def test_save_canonical_raster_preserves_matching_png_bytes(tmp_path) -> None:
    output = tmp_path / "figure.png"
    image = Image.new("RGB", (5, 3), "white")
    image.putpixel((2, 1), (12, 34, 56))
    image.save(output, format="PNG", dpi=(300, 300), compress_level=0)
    original = output.read_bytes()

    assert save_canonical_raster(image, output, 300) is False
    assert output.read_bytes() == original

    changed = image.copy()
    changed.putpixel((2, 1), (65, 43, 21))
    assert save_canonical_raster(changed, output, 300) is True
    assert output.read_bytes() != original

    with Image.open(output) as rebuilt:
        assert rebuilt.convert("RGB").tobytes() == changed.tobytes()
        assert all(abs(value - 300) < 0.01 for value in rebuilt.info["dpi"])


def test_save_canonical_raster_rewrites_non_rgb_png(tmp_path) -> None:
    output = tmp_path / "figure.png"
    rgb = Image.new("RGB", (3, 2), (12, 34, 56))
    rgba = rgb.convert("RGBA")
    rgba.save(output, format="PNG", dpi=(300, 300))

    assert save_canonical_raster(rgb, output, 300) is True
    with Image.open(output) as rebuilt:
        assert rebuilt.mode == "RGB"
        assert rebuilt.tobytes() == rgb.tobytes()
