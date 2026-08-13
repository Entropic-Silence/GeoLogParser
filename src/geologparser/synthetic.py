"""Deterministic synthetic borehole-log generator with known labels.

Synthetic records are useful for controlled robustness and pipeline smoke tests;
they are never silently promoted to real or human Ground Truth.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any

from geologparser.io import empty_borehole_record, empty_interval, field


LITHOLOGIES = ("clay", "silt", "sand", "gravel", "mudstone", "sandstone")
DESCRIPTIONS = ("brown, moist, stiff", "gray, dense", "yellow, medium dense", "weathered, fractured")


def _label(value: Any, source_text: str | None = None, unit: str | None = None) -> dict[str, Any]:
    return field(
        value, source_page=1, source_bbox=None,
        source_text=source_text if source_text is not None else str(value),
        extraction_method="synthetic_ground_truth", confidence=1.0,
        validation_status="synthetic_verified", raw_unit=unit,
    )


def make_synthetic_record(index: int, rng: random.Random, *, template_id: str) -> dict[str, Any]:
    identifier = f"SYN-{index:04d}"
    count = rng.randint(2, 6)
    depths = [0.0]
    for _ in range(count):
        depths.append(round(depths[-1] + rng.uniform(0.5, 3.5), 2))
    record = empty_borehole_record(identifier, f"synthetic/{identifier}.png", "image")
    record["document"]["source_sha256"] = None
    record["document"]["metadata"].update({
        "template_id": template_id, "project_id": f"SYN-P{index % 8:02d}",
        "source_id": "SYNTHETIC_V001", "quality": "high", "contains_stamp": False,
        "contains_handwriting": False, "dpi": 180,
    })
    record["borehole"].update({
        "borehole_id": _label(identifier),
        "project_name": _label(f"Synthetic Project {index % 8:02d}"),
        "page_id": _label("1"),
        "collar_elevation_m": _label(round(rng.uniform(10, 250), 2), unit="m"),
        "final_depth_m": _label(depths[-1], unit="m"),
        "groundwater_depth_m": _label(round(rng.uniform(0, depths[-1]), 2), unit="m"),
    })
    intervals = []
    for interval_index in range(count):
        top, bottom = depths[interval_index], depths[interval_index + 1]
        item = empty_interval(f"I{interval_index + 1:03d}")
        lithology = LITHOLOGIES[(index + interval_index) % len(LITHOLOGIES)]
        description = DESCRIPTIONS[(index + interval_index) % len(DESCRIPTIONS)]
        item["top_depth_m"] = _label(top, f"{top:.2f}", "m")
        item["bottom_depth_m"] = _label(bottom, f"{bottom:.2f}", "m")
        item["thickness_m"] = _label(round(bottom - top, 2), f"{bottom - top:.2f}", "m")
        item["lithology_raw"] = _label(lithology)
        item["lithology_normalized"] = _label(lithology)
        item["description_raw"] = _label(description)
        item["description_normalized"] = _label(description)
        intervals.append(item)
    record["intervals"] = intervals
    return record


def _render_page(record: dict[str, Any], path: Path, *, template_id: str, rng: random.Random, dpi: int) -> dict[str, Any]:
    """Render a simple table-like page using Pillow, returning degradation metadata."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    except ImportError as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("synthetic rendering requires Pillow") from exc
    width, height = (1400, 1900) if template_id.endswith("A") else (1200, 1700)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    draw.text((60, 45), "BOREHOLE LOG", fill="black", font=font)
    draw.text((60, 95), f"ID: {record['borehole']['borehole_id']['value']}", fill="black", font=small)
    draw.text((60, 135), f"Final depth: {record['borehole']['final_depth_m']['value']:.2f} m", fill="black", font=small)
    left, top, right = 60, 220, width - 60
    cols = [left, left + 170, left + 370, left + 570, right]
    draw.line((left, top, right, top), fill="black", width=3)
    headers = ["Top m", "Bottom m", "Thickness m", "Lithology"]
    for x, text in zip(cols[:-1], headers):
        draw.text((x + 8, top + 12), text, fill="black", font=small)
    row_height = 150
    for index, interval in enumerate(record["intervals"]):
        y = top + 65 + index * row_height
        draw.line((left, y, right, y), fill="black", width=2)
        values = [interval["top_depth_m"]["value"], interval["bottom_depth_m"]["value"], interval["thickness_m"]["value"], interval["lithology_raw"]["value"]]
        for x, value in zip(cols[:-1], values):
            text = f"{value:.2f}" if isinstance(value, float) else str(value)
            draw.text((x + 8, y + 22), text, fill="black", font=small)
        draw.text((cols[3] + 8, y + 62), interval["description_raw"]["value"], fill="black", font=small)
    bottom = top + 65 + len(record["intervals"]) * row_height
    for x in cols:
        draw.line((x, top, x, bottom), fill="black", width=2)
    draw.line((left, bottom, right, bottom), fill="black", width=3)
    blur_radius = round(rng.choice((0.0, 0.0, 0.4, 0.8)), 2)
    rotation = rng.choice((0.0, 0.0, -1.2, 1.2))
    noise_level = rng.choice((0, 0, 3, 8))
    jpeg_quality = rng.choice((95, 95, 80, 60))
    if blur_radius:
        image = image.filter(ImageFilter.GaussianBlur(blur_radius))
    if rotation:
        image = image.rotate(rotation, expand=True, fillcolor="white")
    if noise_level:
        pixels = image.load()
        for _ in range(int(width * height * noise_level / 10000)):
            x, y = rng.randrange(image.width), rng.randrange(image.height)
            base = pixels[x, y]
            delta = rng.randint(-noise_level, noise_level)
            pixels[x, y] = tuple(max(0, min(255, channel + delta)) for channel in base)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", dpi=(dpi, dpi), optimize=False)
    return {
        "blur_sigma": blur_radius, "rotation_angle_degrees": rotation,
        "noise_level": noise_level, "jpeg_quality_control": jpeg_quality,
        "render_width_px": image.width, "render_height_px": image.height,
    }


def generate_synthetic_dataset(output_root: Path, *, count: int = 32, seed: int = 20260813, templates: int = 8, dpi: int = 180) -> dict[str, Any]:
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise FileExistsError(f"synthetic dataset already exists: {output_root}")
    if count < 1 or templates < 1:
        raise ValueError("count and templates must be positive")
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    rng = random.Random(seed)
    rows = []
    try:
        for index in range(1, count + 1):
            template_id = f"SYN-T{(index - 1) % templates + 1:02d}{'A' if index % 2 else 'B'}"
            record = make_synthetic_record(index, rng, template_id=template_id)
            image_path = temporary / "images" / f"SYN-{index:04d}.png"
            degradation = _render_page(record, image_path, template_id=template_id, rng=rng, dpi=dpi)
            record_path = temporary / "labels" / f"SYN-{index:04d}.json"
            record_path.parent.mkdir(parents=True, exist_ok=True)
            record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            rows.append({
                "record_id": f"SYN-{index:04d}", "image_path": str(output_root / "images" / f"SYN-{index:04d}.png"),
                "label_path": str(output_root / "labels" / f"SYN-{index:04d}.json"),
                "ground_truth_tier": "SYNTHETIC", "template_id": template_id,
                "project_id": record["document"]["metadata"]["project_id"], "source_id": "SYNTHETIC_V001",
                "source_sha256": None, "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
                "label_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
                "degradation": degradation,
            })
        manifest = temporary / "manifest.jsonl"
        manifest.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        summary = {
            "dataset_version": "synthetic_borehole_logs_v001", "ground_truth_tier": "SYNTHETIC",
            "count": count, "template_count": templates, "seed": seed, "dpi": dpi,
            "scope": "controlled synthetic extraction/robustness; not real benchmark evidence",
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "label_count": count, "human_ground_truth_count": 0,
        }
        (temporary / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output_root.parent.mkdir(parents=True, exist_ok=True)
        import os
        os.replace(temporary, output_root)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
