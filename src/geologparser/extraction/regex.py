"""Conservative regex baseline over page-aware text regions."""

from __future__ import annotations

import hashlib
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from geologparser.io.records import empty_borehole_record, empty_interval, field
from geologparser.ocr.base import TextRegion


NUMBER = r"[-+]?\d+(?:\.\d+)?"
HEADER_PATTERNS = {
    "borehole_id": re.compile(r"(?:钻\s*孔\s*编\s*号|钻\s*孔\s*号|孔\s*号|borehole\s*(?:id|no\.?)|BGS\s*Reference)\s*[:：]?\s*([A-Za-z0-9_./-]+)", re.I),
    "collar_elevation_m": re.compile(rf"(?:孔\s*口\s*高\s*程|孔\s*口\s*标\s*高|collar\s*elevation)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
    "final_depth_m": re.compile(rf"(?:终\s*孔\s*深\s*度|孔\s*深|final\s*depth)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
    "groundwater_depth_m": re.compile(rf"(?:稳\s*定\s*水\s*位\s*深\s*度|地下水(?:位)?埋深|water\s*depth)\s*[:：]?\s*({NUMBER})\s*(?:m|米)?", re.I),
}
PROJECT_NAME_PATTERN = re.compile(
    r"工程\s*名称\s*[:：]?\s*(.+?)(?=工\s*程\s*编\s*号|$)", re.I,
)
COORDINATE_PATTERNS = {
    "x_coordinate": re.compile(rf"\bX\s*=\s*({NUMBER})", re.I),
    "y_coordinate": re.compile(rf"\bY\s*=\s*({NUMBER})", re.I),
}
DRILLING_DATE_PATTERN = re.compile(
    r"终\s*孔\s*日\s*期\s*[:：]?\s*(\d{4})\s*[/年.-]\s*(\d{1,2})\s*[/月.-]\s*(\d{1,2})\s*日?",
)
BRITISH_GRID_PATTERN = re.compile(
    rf"British\s*National\s*Grid\s*\((\d+)\)\s*[:：]\s*({NUMBER})\s*[,，]\s*({NUMBER})",
    re.I,
)
INTERVAL_PATTERN = re.compile(
    rf"^\s*({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+([^\d\s][^\s]*)\s*(.*)$"
)
NATIVE_STRATUM_ROW_PATTERN = re.compile(
    rf"([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})(?=\s|$)"
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
    methods = {region.method for region in region_list}
    document_type = (
        "mixed_pdf" if extension == ".pdf" and {"direct_pdf_text", "ocr"} <= methods else
        "native_pdf" if extension == ".pdf" and "direct_pdf_text" in methods else
        "scanned_pdf" if extension == ".pdf" else "image"
    )
    record = empty_borehole_record(source_path.stem, str(source_path), document_type)
    if source_path.exists():
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        record["document"]["source_sha256"] = digest
    record["document"]["page_count"] = max((r.page for r in region_list), default=1)
    record["document"]["bbox_coordinate_space"] = "pdf_points" if document_type == "native_pdf" else "pixels"

    for region in region_list:
        collapsed = re.sub(r"\s+", " ", region.text).strip()
        search_units = list(dict.fromkeys(
            list(region.text.splitlines()) + ([collapsed] if collapsed else [])
        ))
        for line in search_units:
            grid_match = BRITISH_GRID_PATTERN.search(line)
            if grid_match:
                coordinate_system, x_value, y_value = grid_match.groups()
                record["borehole"]["coordinate_system"] = _evidence_field(
                    f"EPSG:{coordinate_system}", grid_match.group(0), region
                )
                record["borehole"]["x_coordinate"] = _evidence_field(
                    float(x_value), x_value, region
                )
                record["borehole"]["y_coordinate"] = _evidence_field(
                    float(y_value), y_value, region
                )
            if record["borehole"]["project_name"]["value"] is None:
                project_match = PROJECT_NAME_PATTERN.search(line)
                if project_match:
                    project_name = project_match.group(1).strip(" :：")
                    if project_name not in {"图件名称", "工程编号", "项目名称"}:
                        record["borehole"]["project_name"] = _evidence_field(
                            project_name, project_match.group(0), region,
                        )
            for name, pattern in COORDINATE_PATTERNS.items():
                if record["borehole"][name]["value"] is not None:
                    continue
                coordinate_match = pattern.search(line)
                if coordinate_match:
                    record["borehole"][name] = _evidence_field(
                        float(coordinate_match.group(1)), coordinate_match.group(1), region,
                    )
            if record["borehole"]["drilling_date"]["value"] is None:
                date_match = DRILLING_DATE_PATTERN.search(line)
                if date_match:
                    try:
                        normalized_date = date(*(int(part) for part in date_match.groups())).isoformat()
                    except ValueError:
                        normalized_date = None
                    if normalized_date is not None:
                        record["borehole"]["drilling_date"] = _evidence_field(
                            normalized_date, date_match.group(0), region,
                        )
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
        native_row_match = NATIVE_STRATUM_ROW_PATTERN.search(collapsed)
        if native_row_match:
            code, elevation_text, bottom_text, thickness_text = native_row_match.groups()
            bottom = Decimal(bottom_text)
            thickness = Decimal(thickness_text)
            top = bottom - thickness
            item = empty_interval(f"I{len(record['intervals']) + 1:03d}")
            item["top_depth_m"] = field(
                float(top), source_page=region.page,
                source_bbox=list(region.bbox) if region.bbox else None,
                source_text=f"{bottom_text} - {thickness_text}", extraction_method="derived",
                confidence=_confidence(region), validation_status="not_validated", raw_unit="m",
            )
            item["bottom_depth_m"] = _evidence_field(float(bottom), bottom_text, region, "m")
            item["thickness_m"] = _evidence_field(float(thickness), thickness_text, region, "m")
            item["stratum_code_raw"] = _evidence_field(code, code, region)
            # Elevation is not part of the v001 interval schema. It remains in
            # source_text and is not silently repurposed as a depth.
            item["bottom_depth_m"]["source_text"] = f"elevation={elevation_text}; bottom={bottom_text}"
            record["intervals"].append(item)
    return record
