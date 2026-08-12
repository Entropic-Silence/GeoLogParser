"""Seeded image degradations with fully recorded parameters."""

from __future__ import annotations

import hashlib
import io
import random
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DegradationConfig:
    resolution_scale: float = 1.0
    blur_radius: float = 0.0
    gaussian_noise_std: float = 0.0
    rotation_degrees: float = 0.0
    jpeg_quality: int | None = None
    contrast: float = 1.0
    broken_line_count: int = 0
    broken_line_width_px: int = 3
    watermark_text: str | None = None
    watermark_opacity: int = 48
    stamp_count: int = 0
    occlusion_fraction: float = 0.0
    seed: int = 42


def degrade_image(source: Path, destination: Path, config: DegradationConfig) -> dict:
    if config.resolution_scale <= 0 or config.resolution_scale > 1:
        raise ValueError("resolution_scale must be within (0, 1]")
    if config.blur_radius < 0 or config.gaussian_noise_std < 0 or config.contrast < 0:
        raise ValueError("blur, noise, and contrast parameters must be non-negative")
    if config.jpeg_quality is not None and not 1 <= config.jpeg_quality <= 100:
        raise ValueError("jpeg_quality must be within [1, 100]")
    if config.broken_line_count < 0 or config.broken_line_width_px <= 0:
        raise ValueError("broken-line count must be non-negative and width positive")
    if not 0 <= config.watermark_opacity <= 255:
        raise ValueError("watermark_opacity must be within [0, 255]")
    if config.stamp_count < 0:
        raise ValueError("stamp_count must be non-negative")
    if not 0 <= config.occlusion_fraction <= 0.5:
        raise ValueError("occlusion_fraction must be within [0, 0.5]")
    try:
        from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
    except ImportError as exc:
        raise RuntimeError("degradation requires Pillow") from exc
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    original_width, original_height = image.size
    if config.resolution_scale != 1:
        downsampled = (
            max(1, round(original_width * config.resolution_scale)),
            max(1, round(original_height * config.resolution_scale)),
        )
        image = image.resize(downsampled, resample=Image.Resampling.LANCZOS)
        image = image.resize((original_width, original_height), resample=Image.Resampling.BICUBIC)
    if config.blur_radius:
        image = image.filter(ImageFilter.GaussianBlur(config.blur_radius))
    if config.gaussian_noise_std:
        rng = random.Random(config.seed)
        pixels = []
        for pixel in image.getdata():
            pixels.append(tuple(
                max(0, min(255, round(channel + rng.gauss(0, config.gaussian_noise_std))))
                for channel in pixel
            ))
        image.putdata(pixels)
    if config.contrast != 1:
        image = ImageEnhance.Contrast(image).enhance(config.contrast)
    if config.rotation_degrees:
        image = image.rotate(config.rotation_degrees, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    rng = random.Random(config.seed + 1)
    if config.broken_line_count:
        draw = ImageDraw.Draw(image)
        for _ in range(config.broken_line_count):
            if rng.random() < 0.5:
                y = rng.randrange(image.height)
                start = rng.randrange(max(1, image.width - 1))
                length = rng.randint(max(1, image.width // 30), max(2, image.width // 8))
                draw.line((start, y, min(image.width - 1, start + length), y), fill="white", width=config.broken_line_width_px)
            else:
                x = rng.randrange(image.width)
                start = rng.randrange(max(1, image.height - 1))
                length = rng.randint(max(1, image.height // 30), max(2, image.height // 8))
                draw.line((x, start, x, min(image.height - 1, start + length)), fill="white", width=config.broken_line_width_px)
    if config.watermark_text:
        overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        font = ImageFont.load_default(size=max(12, image.width // 28))
        text_box = draw.textbbox((0, 0), config.watermark_text, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        spacing_x, spacing_y = max(1, text_width * 2), max(1, text_height * 6)
        for y in range(-image.height, image.height * 2, spacing_y):
            for x in range(-image.width, image.width * 2, spacing_x):
                draw.text((x, y), config.watermark_text, font=font, fill=(110, 110, 110, config.watermark_opacity))
        overlay = overlay.rotate(25, resample=Image.Resampling.BICUBIC, expand=False)
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    if config.stamp_count:
        draw = ImageDraw.Draw(image, "RGBA")
        for index in range(config.stamp_count):
            radius = max(12, min(image.size) // 12)
            cx = rng.randint(radius, max(radius, image.width - radius))
            cy = rng.randint(radius, max(radius, image.height - radius))
            draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=(190, 20, 20, 145), width=max(2, radius // 12))
            draw.line((cx-radius, cy, cx+radius, cy), fill=(190, 20, 20, 100), width=max(1, radius // 18))
            draw.text((cx-radius//2, cy-radius//4), f"S{index+1}", fill=(190, 20, 20, 145))
    if config.occlusion_fraction:
        draw = ImageDraw.Draw(image)
        target_area = image.width * image.height * config.occlusion_fraction
        aspect = rng.uniform(0.5, 2.0)
        width = min(image.width, max(1, round((target_area * aspect) ** 0.5)))
        height = min(image.height, max(1, round(target_area / width)))
        x = rng.randint(0, max(0, image.width - width))
        y = rng.randint(0, max(0, image.height - height))
        draw.rectangle((x, y, x + width, y + height), fill="white")
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {"quality": config.jpeg_quality} if config.jpeg_quality is not None else {}
    image.save(destination, **save_kwargs)
    return {
        "source_path": str(source), "destination_path": str(destination),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "destination_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "parameters": asdict(config), "width": image.width, "height": image.height,
        "operation_order": [
            "resolution", "blur", "gaussian_noise", "contrast", "rotation",
            "broken_lines", "watermark", "stamp", "partial_occlusion", "encoding",
        ],
    }
