"""Conservative regex baseline over page-aware text regions."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from geologparser.io.records import empty_borehole_record, empty_interval, field
from geologparser.ocr.base import TextRegion


NUMBER = r"[-+]?\d+(?:\.\d+)?"
HEADER_PATTERNS = {
    "borehole_id": re.compile(r"(?:钻孔编号|钻孔号|孔号|borehole\s*(?:id|no\.?))\s*[:：]?\s*([A-Za-z0-9_.-]+)", re.I),
    "collar_elevation_m": re.compile(rf"(?:孔口高程|孔口标高|collar\s*elevation)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
    "final_depth_m": re.compile(rf"(?:终孔深度|孔深|final\s*depth)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
    "groundwater_depth_m": re.compile(rf"(?:地下水(?:位)?埋深|water\s*depth)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
}
INTERVAL_PATTERN = re.compile(
    rf"^\s*({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+([^\d\s][^\s]*)\s*(.*)$"
)


def _confidence(region: TextRegion) -> float | None:
    return None if region.confidence is None else max(0.0, min(1.0, region.confidence))


def _evidence_field(value, source_text: str, region: TextRegion, raw_unit: str | None = None):
    return field(
        value,
        source_page=region.page,
        source_bbox=list(region.bbox) if region.bbox else None,
        source_text=source_text,
        extraction_method="regex",
        confidence=_confidence(region),
        validation_status="not_validated",
        raw_unit=raw_unit,
    )


def extract_structured(regions: Iterable[TextRegion], source_path: Path) -> dict:
    region_list = list(regions)
    extension = source_path.suffix.lower()
    document_type = "native_pdf" if extension == ".pdf" and any(r.method == "direct_pdf_text" for r in region_list) else (
        "scanned_pdf" if extension == ".pdf" else "image"
    )
    record = empty_borehole_record(source_path.stem, str(source_path), document_type)
    if source_path.exists():
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        record["document"]["source_sha256"] = digest
    record["document"]["page_count"] = max((r.page for r in region_list), default=1)
    record["document"]["bbox_coordinate_space"] = "pdf_points" if document_type == "native_pdf" else "pixels"

    for region in region_list:
        for line in region.text.splitlines():
            for name, pattern in HEADER_PATTERNS.items():
                if record["borehole"][name]["value"] is not None:
                    continue
                match = pattern.search(line)
                if not match:
                    continue
                raw_value = match.group(1)
                value = raw_value if name == "borehole_id" else float(raw_value)
                record["borehole"][name] = _evidence_field(
                    value, match.group(0), region, None if name == "borehole_id" else "m"
                )

            match = INTERVAL_PATTERN.match(line)
            if match:
                item = empty_interval(f"I{len(record['intervals']) + 1:03d}")
                for name, value in zip(("top_depth_m", "bottom_depth_m", "thickness_m"), match.groups()[:3]):
                    item[name] = _evidence_field(float(value), value, region, "m")
                lithology = match.group(4).strip()
                description = match.group(5).strip() or None
                item["lithology_raw"] = _evidence_field(lithology, lithology, region)
                if description is not None:
                    item["description_raw"] = _evidence_field(description, description, region)
                record["intervals"].append(item)
    return record

