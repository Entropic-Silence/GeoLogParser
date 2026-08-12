"""Entity-level coverage audit for LibreDWG review SVGs.

The audit deliberately does not repair unsupported entities.  In particular,
inserting MTEXT with an inferred coordinate transform would make an entity ID
appear covered without establishing that the text is in the correct place.
Missing renderer output therefore remains explicit review evidence.
"""

from __future__ import annotations

from collections import Counter
from io import BytesIO
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


NON_VISUAL_ENTITIES = {"BLOCK", "ENDBLK"}
VIEWBOX_PATTERN = re.compile(r"\bviewBox\s*=\s*['\"]([^'\"]+)['\"]")


def graphical_entities(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        item for item in payload.get("OBJECTS", ())
        if item.get("entity") and item.get("entity") not in NON_VISUAL_ENTITIES
    ]


def audit_svg_geometry(svg: str, *, absolute_coordinate_limit: float = 1e15) -> dict[str, Any]:
    """Check whether an SVG viewBox is usable without claiming visual fidelity.

    LibreDWG can return success while emitting its approximately ``1e20``
    sentinel bounds and a negative viewBox size.  This audit catches that
    technical failure before rasterisation.  The generous coordinate limit is
    only a renderer-sanity guard; plausible engineering/project coordinates
    remain well below it.
    """
    match = VIEWBOX_PATTERN.search(svg)
    reasons: list[str] = []
    values: list[float] | None = None
    if not match:
        reasons.append("missing_viewbox")
    else:
        try:
            values = [float(value) for value in re.split(r"[\s,]+", match.group(1).strip())]
        except ValueError:
            reasons.append("non_numeric_viewbox")
        if values is not None:
            if len(values) != 4:
                reasons.append("viewbox_requires_four_values")
            elif not all(math.isfinite(value) for value in values):
                reasons.append("non_finite_viewbox")
            else:
                _, _, width, height = values
                if width <= 0 or height <= 0:
                    reasons.append("non_positive_viewbox_extent")
                if any(abs(value) > absolute_coordinate_limit for value in values):
                    reasons.append("viewbox_exceeds_renderer_sanity_limit")
    return {
        "viewbox": values,
        "absolute_coordinate_limit": absolute_coordinate_limit,
        "geometry_sanity_passed": not reasons,
        "failure_reasons": reasons,
        "interpretation": "technical rasterisation precheck; not visual fidelity",
    }


def write_review_png(svg: str, path: Path, output_width: int) -> dict[str, Any]:
    """Rasterise and trim review content, or write an explicit failure card."""
    from cairosvg import svg2png
    from PIL import Image, ImageDraw

    geometry = audit_svg_geometry(svg)
    crop_box = None
    raster_status = "not_attempted_invalid_svg_geometry"
    placeholder = True
    unique_color_count = None
    nontransparent_bbox = None
    if geometry["geometry_sanity_passed"]:
        raster_status = "transparent_or_empty_raster"
        raster = Image.open(BytesIO(svg2png(bytestring=svg.encode("utf-8"), output_width=output_width))).convert("RGBA")
        nontransparent_bbox = raster.getchannel("A").getbbox()
        colors = raster.getcolors(maxcolors=1_000_000)
        unique_color_count = len(colors) if colors is not None else ">1000000"
        if nontransparent_bbox is not None:
            left, top, right, bottom = nontransparent_bbox
            padding = max(8, round(max(right - left, bottom - top) * 0.02))
            crop_box = [
                max(0, left - padding), max(0, top - padding),
                min(raster.width, right + padding), min(raster.height, bottom + padding),
            ]
            raster = raster.crop(tuple(crop_box))
            raster.save(path)
            raster_status = "nontransparent_content_detected_and_trimmed"
            placeholder = False
    if placeholder:
        raster = Image.new("RGB", (output_width, 360), "#15191d")
        draw = ImageDraw.Draw(raster)
        draw.rectangle((12, 12, output_width - 13, 347), outline="#dc554f", width=4)
        draw.multiline_text(
            (42, 50),
            "GeoLogParser CAD REVIEW DERIVATIVE UNAVAILABLE\n\n"
            f"Raster status: {raster_status}\n"
            f"Geometry failures: {', '.join(geometry['failure_reasons']) or 'none'}\n\n"
            "Do not use this placeholder for annotation or visual completeness review.",
            fill="white", spacing=12,
        )
        raster.save(path)
    return {
        "geometry_audit": geometry,
        "raster_content_status": raster_status,
        "raster_is_placeholder": placeholder,
        "pretrim_nontransparent_bbox": list(nontransparent_bbox) if nontransparent_bbox else None,
        "crop_box": crop_box,
        "pretrim_unique_color_count": unique_color_count,
        "pixel_dimensions": [raster.width, raster.height],
    }


def entity_coverage(svg: str, entities: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compare source graphical entity indexes with renderer-emitted IDs.

    ID coverage is a structural diagnostic only.  It is not evidence of
    correct geometry, text encoding, fonts, colours, clipping, or visual
    fidelity.
    """
    source = {int(entity["index"]): str(entity["entity"]) for entity in entities}
    rendered = {int(value) for value in re.findall(r'id=["\']dwg-object-(\d+)["\']', svg)}
    covered = set(source) & rendered
    missing = set(source) - rendered
    extra = rendered - set(source)
    missing_types = Counter(source[index] for index in missing)
    return {
        "source_entity_count": len(source),
        "rendered_source_entity_count": len(covered),
        "entity_coverage": len(covered) / len(source) if source else None,
        "missing_entity_count": len(missing),
        "missing_entity_type_counts": dict(sorted(missing_types.items())),
        "missing_entity_indexes": sorted(missing),
        "extra_rendered_id_count": len(extra),
        "extra_rendered_indexes": sorted(extra),
        "complete_entity_id_coverage": not missing and not extra,
        "coverage_interpretation": "structural ID diagnostic; not visual fidelity",
    }
