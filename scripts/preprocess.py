#!/usr/bin/env python3
"""Apply one deterministic degradation configuration and emit trace metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from geologparser.preprocessing import DegradationConfig, degrade_image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--resolution-scale", type=float, default=1.0)
    parser.add_argument("--blur-radius", type=float, default=0.0)
    parser.add_argument("--noise-std", type=float, default=0.0)
    parser.add_argument("--rotation-degrees", type=float, default=0.0)
    parser.add_argument("--jpeg-quality", type=int)
    parser.add_argument("--contrast", type=float, default=1.0)
    parser.add_argument("--broken-line-count", type=int, default=0)
    parser.add_argument("--watermark-text")
    parser.add_argument("--stamp-count", type=int, default=0)
    parser.add_argument("--occlusion-fraction", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--metadata", type=Path)
    arguments = parser.parse_args()
    result = degrade_image(arguments.source, arguments.destination, DegradationConfig(
        resolution_scale=arguments.resolution_scale, blur_radius=arguments.blur_radius,
        gaussian_noise_std=arguments.noise_std, rotation_degrees=arguments.rotation_degrees,
        jpeg_quality=arguments.jpeg_quality, contrast=arguments.contrast,
        broken_line_count=arguments.broken_line_count, watermark_text=arguments.watermark_text,
        stamp_count=arguments.stamp_count, occlusion_fraction=arguments.occlusion_fraction,
        seed=arguments.seed,
    ))
    if arguments.metadata:
        arguments.metadata.parent.mkdir(parents=True, exist_ok=True)
        arguments.metadata.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
