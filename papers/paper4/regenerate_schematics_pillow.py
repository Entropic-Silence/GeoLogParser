#!/usr/bin/env python3
"""Regenerate schematic Paper 4 figures when Matplotlib is unavailable."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "figures"


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def centered(draw: ImageDraw.ImageDraw, box, text: str, size: int, bold=False, fill="#0f172a"):
    x0, y0, x1, y1 = box
    f = font(size, bold)
    lines = text.split("\n")
    heights = [draw.textbbox((0, 0), line, font=f)[3] for line in lines]
    total = sum(heights) + (len(lines) - 1) * 8
    y = (y0 + y1 - total) / 2
    for line, height in zip(lines, heights):
        width = draw.textbbox((0, 0), line, font=f)[2]
        draw.text(((x0 + x1 - width) / 2, y), line, font=f, fill=fill)
        y += height + 8


def arrow(draw, start, end, fill="#475569", width=5):
    draw.line([start, end], fill=fill, width=width)
    x0, y0 = start
    x1, y1 = end
    import math
    angle = math.atan2(y1 - y0, x1 - x0)
    length = 20
    left = (x1 - length * math.cos(angle - 0.45), y1 - length * math.sin(angle - 0.45))
    right = (x1 - length * math.cos(angle + 0.45), y1 - length * math.sin(angle + 0.45))
    draw.polygon([end, left, right], fill=fill)


def dashed(draw, start, end, fill="#64748b", width=4, dash=18, gap=12):
    import math
    x0, y0 = start
    x1, y1 = end
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    distance = 0
    while distance < length:
        end_distance = min(distance + dash, length)
        draw.line(
            [(x0 + ux * distance, y0 + uy * distance),
             (x0 + ux * end_distance, y0 + uy * end_distance)],
            fill=fill, width=width,
        )
        distance += dash + gap


def schematic(path: Path, abstract: bool = False):
    width, height = (1800, 650) if not abstract else (1800, 720)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title = ("From visual extraction to trustworthy database ingestion"
             if abstract else
             "One chain: capability -> evidence -> decision -> support consequence")
    title_font = 34 if abstract else 32
    title_width = draw.textbbox((0, 0), title, font=font(title_font, True))[2]
    draw.text(((width - title_width) / 2, 35), title, font=font(title_font, True), fill="#0f172a")
    labels = [
        (80, 220, 300, 410, "Borehole page" if abstract else "VLM proposal", "visual record" if abstract else "high-recall image -> intervals", "#e2e8f0"),
        (390, 220, 610, 410, "VLM proposal" if abstract else "Independent evidence", "high recall" if abstract else "positioned values\npage + bbox", "#dbeafe" if abstract else "#dcfce7"),
        (700, 220, 920, 410, "Independent\nevidence" if abstract else "Deterministic checks", "page + bbox" if abstract else "units · order\ncolumn ownership", "#dcfce7" if abstract else "#fef3c7"),
        (1010, 155, 1220, 285, "ACCEPT", "auditable row", "#bbf7d0"),
        (1010, 345, 1220, 475, "REVIEW" if abstract else "NEEDS REVIEW", "preserve reason" if abstract else "raw proposal +\nreason preserved", "#fee2e2"),
        (1310, 220, 1690, 410, "Database +\nspatial support" if abstract else "Database + support", "support mask" if abstract else "accepted rows ->\nsupport mask", "#e0e7ff"),
    ]
    for x0, y0, x1, y1, heading, body, color in labels:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=color, outline="#334155", width=3)
        centered(draw, (x0 + 10, y0 + 15, x1 - 10, y1 - 80), heading, 25, True)
        centered(draw, (x0 + 10, y0 + 95, x1 - 10, y1 - 15), body, 19, False, "#334155")
    for start, end in [
        ((300, 315), (390, 315)), ((610, 315), (700, 315)),
        ((920, 315), (1010, 220)), ((920, 315), (1010, 410)),
        ((1220, 220), (1310, 315)), ((1220, 410), (1310, 315)),
    ]:
        arrow(draw, start, end)
    if not abstract:
        draw.rounded_rectangle((700, 500, 920, 610), radius=18, fill="#f1f5f9", outline="#64748b", width=3)
        centered(draw, (710, 510, 910, 600), "Legacy recovery\nsecondary harm analysis", 18, True, "#334155")
        dashed(draw, (810, 410), (810, 500))
        draw.text((80, 150), "RQ1 / CAPABILITY", font=font(20, True), fill="#1d4ed8")
        draw.text((390, 150), "RQ2 / ASSURANCE", font=font(20, True), fill="#15803d")
        draw.text((1310, 150), "RQ3 / CONSEQUENCE", font=font(20, True), fill="#4338ca")
        footer = "Dashed branch: legacy sequence reconstruction is secondary harm analysis, not the main assurance path."
    else:
        footer = "0.993 precision @ 24.4% proposal coverage  |  4/100 complete documents auto-accepted"
    footer_width = draw.textbbox((0, 0), footer, font=font(20))[2]
    draw.text(((width - footer_width) / 2, height - 45), footer, font=font(20), fill="#334155")
    image.save(path, dpi=(300, 300))
    image.save(path.with_suffix(".pdf"), "PDF", resolution=300.0)


def annotate_existing():
    """Update narrative labels on frozen F2/F4 raster plots without changing data."""
    f2_path = OUT / "F2_vlm_source_shift.png"
    if f2_path.exists():
        image = Image.open(f2_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, image.width, 165), fill="white")
        title = "Capability and transport are separate evidence questions"
        draw.text(((image.width - draw.textbbox((0, 0), title, font=font(34, True))[2]) / 2, 18),
                  title, font=font(34, True), fill="#0f172a")
        draw.text((305, 128), "Familiar source: five record-disjoint cohorts",
                  font=font(26, True), fill="#0f172a")
        draw.text((1350, 128), "Source shift: declared evidence tiers",
                  font=font(26, True), fill="#0f172a")
        draw.text((305, 154), "Published manual-transcription Gold",
                  font=font(16), fill="#334155")
        draw.text((1350, 154), "Source-agreement/stress panels; not pooled with Gold",
                  font=font(16), fill="#334155")
        image.save(f2_path, dpi=(300, 300))

    f4_path = OUT / "F4_spatial_support_consequence.png"
    if f4_path.exists():
        image = Image.open(f4_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, image.width, 205), fill="white")
        title = "Abstention changes the geoscientific observation set"
        draw.text(((image.width - draw.textbbox((0, 0), title, font=font(34, True))[2]) / 2, 18),
                  title, font=font(34, True), fill="#0f172a")
        draw.text((210, 112), "Distinct estimands", font=font(26, True), fill="#0f172a")
        draw.text((210, 139), "Full support uses each policy's retained points",
                  font=font(15), fill="#334155")
        draw.text((1168, 112), "Retained hull/support area", font=font(26, True), fill="#0f172a")
        draw.text((1870, 112), "Support spacing", font=font(26, True), fill="#0f172a")
        draw.text((1145, 180), "1.000", font=font(18), fill="#0f172a")
        image.save(f4_path, dpi=(300, 300))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    schematic(OUT / "F1_trustworthy_framework.png")
    schematic(OUT / "graphical_abstract.png", abstract=True)
    annotate_existing()
    manifest_path = OUT.parent / "figure_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["graphical_abstract"] = {
        "file": "figures/graphical_abstract.pdf",
        "purpose": "schematic overview of proposal, evidence, decision, and support",
        "rights": "programmatic schematic; no source-page image used",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
