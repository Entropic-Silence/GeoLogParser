#!/usr/bin/env python3
"""Link source-provided Padova KML borehole locations to the PDF inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile


KML = {"kml": "http://www.opengis.net/kml/2.2"}
BOREHOLE_PATTERN = re.compile(r"^(?:GS\d+|PS\d+|TS\d+|TPS\d+)$", re.IGNORECASE)


def canonical_id(value: str) -> str:
    match = re.fullmatch(r"([A-Za-z]+)0*(\d+)", value.strip())
    if not match:
        return value.strip().upper()
    return f"{match.group(1).upper()}{int(match.group(2))}"


def parse_kmz(kmz_path: Path) -> list[dict]:
    with ZipFile(kmz_path) as archive:
        kml_names = [name for name in archive.namelist() if name.lower().endswith(".kml")]
        if len(kml_names) != 1:
            raise ValueError(f"expected one KML document, found {len(kml_names)}")
        root = ET.fromstring(archive.read(kml_names[0]))
    rows = []
    for placemark in root.findall(".//kml:Placemark", KML):
        raw_id = (placemark.findtext("kml:name", default="", namespaces=KML)).strip()
        coordinates = placemark.findtext(".//kml:Point/kml:coordinates", namespaces=KML)
        if not raw_id or not coordinates:
            continue
        parts = [float(part) for part in coordinates.strip().split(",")]
        if len(parts) < 2:
            raise ValueError(f"invalid KML point for {raw_id}: {coordinates}")
        rows.append({
            "source_id_raw": raw_id,
            "source_id_canonical": canonical_id(raw_id),
            "longitude": parts[0],
            "latitude": parts[1],
            "altitude": parts[2] if len(parts) > 2 else None,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kmz", type=Path)
    parser.add_argument("pdf_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    arguments = parser.parse_args()
    pdf_rows = [json.loads(line) for line in arguments.pdf_manifest.read_text(encoding="utf-8").splitlines()]
    locations = parse_kmz(arguments.kmz)
    boreholes = {
        row["source_id_canonical"]: row
        for row in locations
        if BOREHOLE_PATTERN.fullmatch(row["source_id_canonical"])
    }
    output = []
    missing = []
    for pdf in pdf_rows:
        path = Path(pdf["local_path"])
        identifier = canonical_id(path.stem)
        location = boreholes.get(identifier)
        if not location:
            missing.append(identifier)
            continue
        warning_codes = []
        if identifier == "TS5":
            warning_codes.append("SOURCE_FILENAME_HEADER_ID_CONFLICT_KNOWN")
        output.append({
            "source_record_id": pdf["source_record_id"],
            "pdf_filename": path.name,
            "pdf_sha256": pdf["sha256"],
            "link_key": identifier,
            "location_id_raw": location["source_id_raw"],
            "longitude": location["longitude"],
            "latitude": location["latitude"],
            "coordinate_system": "EPSG:4326",
            "coordinate_source": "source_repository_kmz",
            "coordinate_validation_status": "source_provided_unverified",
            "warning_codes": warning_codes,
        })
    if missing:
        raise ValueError(f"PDFs without source-provided locations: {sorted(missing)}")
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = arguments.output_dir / "borehole_locations.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output),
        encoding="utf-8",
    )
    kmz_sha256 = hashlib.sha256(arguments.kmz.read_bytes()).hexdigest()
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    summary = {
        "scope": "source-provided location linkage; not human Ground Truth",
        "pdf_documents": len(pdf_rows),
        "linked_documents": len(output),
        "coordinate_system": "EPSG:4326",
        "source_kmz_sha256": kmz_sha256,
        "source_pdf_manifest_sha256": hashlib.sha256(arguments.pdf_manifest.read_bytes()).hexdigest(),
        "location_manifest_sha256": manifest_sha256,
        "known_id_conflicts": sum(bool(row["warning_codes"]) for row in output),
        "accuracy_metrics": None,
    }
    (arguments.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
