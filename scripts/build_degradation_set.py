#!/usr/bin/env python3
"""Build an immutable, parameterized robustness image set from a panel manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.preprocessing import DegradationConfig, degrade_image


PROFILES = {
    "resolution_075": DegradationConfig(resolution_scale=.75),
    "resolution_050": DegradationConfig(resolution_scale=.50),
    "resolution_025": DegradationConfig(resolution_scale=.25),
    "blur_10": DegradationConfig(blur_radius=1.0),
    "blur_20": DegradationConfig(blur_radius=2.0),
    "noise_08": DegradationConfig(gaussian_noise_std=8.0),
    "noise_16": DegradationConfig(gaussian_noise_std=16.0),
    "skew_10": DegradationConfig(rotation_degrees=1.0),
    "skew_30": DegradationConfig(rotation_degrees=3.0),
    "jpeg_70": DegradationConfig(jpeg_quality=70),
    "jpeg_30": DegradationConfig(jpeg_quality=30),
    "contrast_070": DegradationConfig(contrast=.70),
    "contrast_040": DegradationConfig(contrast=.40),
    "broken_lines_10": DegradationConfig(broken_line_count=10, broken_line_width_px=4),
    "watermark_48": DegradationConfig(watermark_text="ROBUSTNESS AUDIT", watermark_opacity=48),
    "stamp_1": DegradationConfig(stamp_count=1),
    "occlusion_002": DegradationConfig(occlusion_fraction=.02),
    "occlusion_005": DegradationConfig(occlusion_fraction=.05),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel_manifest", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--base-seed", type=int, default=20260812)
    arguments = parser.parse_args()
    if arguments.output_root.exists():
        raise FileExistsError(f"degradation set already exists: {arguments.output_root}")
    arguments.output_root.mkdir(parents=True)
    panels = [json.loads(line) for line in arguments.panel_manifest.read_text(encoding="utf-8").splitlines() if line]
    rows = []
    for panel_index, panel in enumerate(panels):
        source = Path(panel["rendered_path"])
        for profile_index, (profile, base) in enumerate(PROFILES.items()):
            config = DegradationConfig(**({**base.__dict__, "seed": arguments.base_seed + panel_index * 1000 + profile_index}))
            suffix = ".jpg" if config.jpeg_quality is not None else ".png"
            destination = arguments.output_root / "images" / profile / f"{panel['panel_id']}{suffix}"
            metadata = degrade_image(source, destination, config)
            rows.append({
                "item_id": f"{panel['panel_id']}__{profile}", "source_panel_id": panel["panel_id"],
                "profile": profile, **metadata,
            })
    manifest = arguments.output_root / "degradation_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    summary = {
        "scope": "synthetic robustness inputs; no accuracy without human GT",
        "source_panels": len(panels), "profiles": len(PROFILES), "derived_images": len(rows),
        "base_seed": arguments.base_seed,
        "source_panel_manifest_sha256": hashlib.sha256(arguments.panel_manifest.read_bytes()).hexdigest(),
        "degradation_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "accuracy_metrics": None,
    }
    (arguments.output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
