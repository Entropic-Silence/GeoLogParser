"""Seeded image degradations with fully recorded parameters."""

from __future__ import annotations

import hashlib
import io
import random
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class DegradationConfig:
    blur_radius: float = 0.0
    gaussian_noise_std: float = 0.0
    rotation_degrees: float = 0.0
    jpeg_quality: int | None = None
    contrast: float = 1.0
    seed: int = 42


def degrade_image(source: Path, destination: Path, config: DegradationConfig) -> dict:
    if config.blur_radius < 0 or config.gaussian_noise_std < 0 or config.contrast < 0:
        raise ValueError("blur, noise, and contrast parameters must be non-negative")
    if config.jpeg_quality is not None and not 1 <= config.jpeg_quality <= 100:
        raise ValueError("jpeg_quality must be within [1, 100]")
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError as exc:
        raise RuntimeError("degradation requires Pillow") from exc
    with Image.open(source) as opened:
        image = opened.convert("RGB")
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs = {"quality": config.jpeg_quality} if config.jpeg_quality is not None else {}
    image.save(destination, **save_kwargs)
    return {
        "source_path": str(source), "destination_path": str(destination),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "destination_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "parameters": asdict(config), "width": image.width, "height": image.height,
    }
