"""Technical raster diagnostics for quarantined CAD review derivatives.

These functions can detect blank output and quantify agreement between two
renderers.  They do not establish visual fidelity, font correctness, privacy
clearance, or benchmark eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from pathlib import Path
from statistics import median
from typing import Any


@dataclass(frozen=True)
class RasterAuditConfig:
    background_threshold: int = 16
    occupancy_width: int = 256
    occupancy_height: int = 1024
    tolerance_pixels: int = 2
    minimum_tolerant_f1: float = 0.50

    def __post_init__(self) -> None:
        if not 0 <= self.background_threshold <= 255:
            raise ValueError("background_threshold must be within [0, 255]")
        if self.occupancy_width < 16 or self.occupancy_height < 16:
            raise ValueError("occupancy dimensions must each be at least 16 pixels")
        if not 0 <= self.tolerance_pixels <= 16:
            raise ValueError("tolerance_pixels must be within [0, 16]")
        if not 0 <= self.minimum_tolerant_f1 <= 1:
            raise ValueError("minimum_tolerant_f1 must be within [0, 1]")


def _image_modules():
    from PIL import Image, ImageChops, ImageFilter, ImageStat

    return Image, ImageChops, ImageFilter, ImageStat


def _background_rgb(image: Any) -> tuple[int, int, int]:
    width, height = image.size
    sample = max(1, min(width, height) // 100)
    pixels = []
    for box in (
        (0, 0, width, sample),
        (0, height - sample, width, height),
        (0, 0, sample, height),
        (width - sample, 0, width, height),
    ):
        pixels.extend(image.crop(box).getdata())
    return tuple(int(median(pixel[channel] for pixel in pixels)) for channel in range(3))


def foreground_mask(path: Path, *, threshold: int = 16) -> tuple[Any, dict[str, Any]]:
    """Return a foreground mask and auditable statistics for one raster."""

    if not path.is_file():
        raise FileNotFoundError(path)
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be within [0, 255]")
    Image, ImageChops, _, ImageStat = _image_modules()
    with Image.open(path) as source:
        image = source.convert("RGBA")
    background_rgb = _background_rgb(image.convert("RGB"))
    background = Image.new("RGBA", image.size, (*background_rgb, 255))
    difference = ImageChops.difference(image, background).convert("RGB")
    maximum_channel = difference.getchannel("R")
    maximum_channel = ImageChops.lighter(maximum_channel, difference.getchannel("G"))
    maximum_channel = ImageChops.lighter(maximum_channel, difference.getchannel("B"))
    color_mask = maximum_channel.point(lambda value: 255 if value > threshold else 0, mode="L")
    alpha_mask = image.getchannel("A").point(lambda value: 255 if value > threshold else 0, mode="L")
    mask = ImageChops.multiply(color_mask, alpha_mask)
    bbox = mask.getbbox()
    foreground_pixels = int(ImageStat.Stat(mask).sum[0] / 255)
    total_pixels = image.width * image.height
    if bbox is None:
        content_dimensions = None
        content_aspect_ratio = None
    else:
        content_dimensions = [bbox[2] - bbox[0], bbox[3] - bbox[1]]
        content_aspect_ratio = content_dimensions[0] / content_dimensions[1]
    return mask, {
        "pixel_dimensions": [image.width, image.height],
        "background_rgb": list(background_rgb),
        "background_threshold": threshold,
        "foreground_pixels": foreground_pixels,
        "foreground_fraction": foreground_pixels / total_pixels,
        "content_bbox_pixels": list(bbox) if bbox is not None else None,
        "content_dimensions": content_dimensions,
        "content_aspect_ratio": content_aspect_ratio,
        "raster_nonblank": bbox is not None and foreground_pixels > 0,
        "interpretation": "technical foreground diagnostic; not visual fidelity",
    }


def normalized_occupancy(mask: Any, width: int, height: int) -> Any:
    """Fit a mask's content into a stable comparison canvas."""

    Image, _, _, _ = _image_modules()
    bbox = mask.getbbox()
    canvas = Image.new("L", (width, height), 0)
    if bbox is None:
        return canvas
    content = mask.crop(bbox)
    scale = min(width / content.width, height / content.height)
    resized_size = (
        max(1, round(content.width * scale)),
        max(1, round(content.height * scale)),
    )
    # CAD linework is frequently one pixel wide.  Nearest-neighbour reduction
    # can sample between those lines and erase them entirely, so aggregate each
    # output cell and retain any non-zero contribution.
    content = content.resize(resized_size, resample=Image.Resampling.BOX)
    content = content.point(lambda value: 255 if value > 0 else 0, mode="L")
    canvas.paste(content, ((width - content.width) // 2, (height - content.height) // 2))
    return canvas


def _count(mask: Any) -> int:
    _, _, _, ImageStat = _image_modules()
    return int(ImageStat.Stat(mask).sum[0] / 255)


def compare_rasters(
    first_path: Path,
    second_path: Path,
    *,
    first_is_placeholder: bool = False,
    second_is_placeholder: bool = False,
    config: RasterAuditConfig | None = None,
) -> dict[str, Any]:
    """Quantify normalized binary overlap between two independent renderers."""

    config = config or RasterAuditConfig()
    _, ImageChops, ImageFilter, _ = _image_modules()
    first_mask, first = foreground_mask(first_path, threshold=config.background_threshold)
    second_mask, second = foreground_mask(second_path, threshold=config.background_threshold)
    result: dict[str, Any] = {
        "first_raster": first,
        "second_raster": second,
        "comparison_grid": [config.occupancy_width, config.occupancy_height],
        "occupancy_resampling": "Pillow BOX then nonzero threshold",
        "tolerance_pixels": config.tolerance_pixels,
        "minimum_tolerant_f1": config.minimum_tolerant_f1,
        "visual_fidelity_status": "not_assessed",
        "interpretation": (
            "Cross-renderer occupancy diagnostic only; overlap does not establish correct "
            "geometry, fonts, text, privacy, rights, or benchmark eligibility."
        ),
    }
    if first_is_placeholder or second_is_placeholder:
        result.update({
            "status": "not_comparable_placeholder",
            "raw_iou": None,
            "tolerant_bidirectional_f1": None,
            "content_aspect_log_ratio": None,
        })
        return result
    if not first["raster_nonblank"] or not second["raster_nonblank"]:
        result.update({
            "status": "not_comparable_blank_raster",
            "raw_iou": None,
            "tolerant_bidirectional_f1": None,
            "content_aspect_log_ratio": None,
        })
        return result

    first_grid = normalized_occupancy(
        first_mask, config.occupancy_width, config.occupancy_height,
    )
    second_grid = normalized_occupancy(
        second_mask, config.occupancy_width, config.occupancy_height,
    )
    intersection = _count(ImageChops.multiply(first_grid, second_grid))
    union = _count(ImageChops.lighter(first_grid, second_grid))
    raw_iou = intersection / union if union else None
    filter_size = 2 * config.tolerance_pixels + 1
    first_dilated = first_grid.filter(ImageFilter.MaxFilter(filter_size))
    second_dilated = second_grid.filter(ImageFilter.MaxFilter(filter_size))
    first_count, second_count = _count(first_grid), _count(second_grid)
    first_covered = _count(ImageChops.multiply(first_grid, second_dilated)) / first_count
    second_covered = _count(ImageChops.multiply(second_grid, first_dilated)) / second_count
    tolerant_f1 = (
        2 * first_covered * second_covered / (first_covered + second_covered)
        if first_covered + second_covered
        else 0.0
    )
    aspect_log_ratio = abs(log(first["content_aspect_ratio"] / second["content_aspect_ratio"]))
    result.update({
        "status": (
            "compared_overlap_at_or_above_threshold"
            if tolerant_f1 >= config.minimum_tolerant_f1
            else "compared_overlap_below_threshold"
        ),
        "raw_iou": raw_iou,
        "first_covered_with_tolerance": first_covered,
        "second_covered_with_tolerance": second_covered,
        "tolerant_bidirectional_f1": tolerant_f1,
        "content_aspect_log_ratio": aspect_log_ratio,
    })
    return result
