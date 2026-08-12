"""Small, fixed-ID BGS OpenGeoscience acquisition adapter.

This adapter never performs an unbounded crawl. Callers must supply explicit
BGS IDs and retain the OGL acknowledgement recorded in the dataset registry.
"""

from __future__ import annotations

import json
import mimetypes
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from .manifest import DatasetFile, sha256_file, write_jsonl


LAYER_URL = "https://map.bgs.ac.uk/arcgis/rest/services/GeoIndex_Onshore/boreholes/MapServer/0/query"
SCAN_URL = "https://api.bgs.ac.uk/sobi-scans/v1/borehole/scans/items/{bgs_id}"
OUT_FIELDS = (
    "REFERENCE,NAME,EASTING,NORTHING,LENGTH,YEAR_KNOWN,LENGTH_SCAN_CAT,"
    "BGS_ID,DATE_UPDATED,SCAN_URL,SCAN_QUALITY"
)


def _get(url: str, timeout: int = 120) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "GeoLogParser/0.0.1 research dataset audit"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_metadata(ids: Iterable[int]) -> dict[int, dict[str, Any]]:
    normalized = sorted(set(int(value) for value in ids))
    if not normalized:
        return {}
    where = "BGS_ID IN (" + ",".join(str(value) for value in normalized) + ")"
    query = urllib.parse.urlencode({
        "where": where,
        "outFields": OUT_FIELDS,
        "returnGeometry": "false",
        "f": "json",
    })
    payload = json.loads(_get(f"{LAYER_URL}?{query}"))
    if "error" in payload:
        raise RuntimeError(f"BGS ArcGIS error: {payload['error']}")
    return {int(item["attributes"]["BGS_ID"]): item["attributes"] for item in payload.get("features", [])}


def download_fixed_sample(ids: Iterable[int], root: Path, access_date: str | None = None) -> Path:
    normalized = sorted(set(int(value) for value in ids))
    metadata = fetch_metadata(normalized)
    missing = sorted(set(normalized) - set(metadata))
    if missing:
        raise ValueError(f"BGS IDs not returned by official layer: {missing}")
    access_date = access_date or date.today().isoformat()
    raw_root = root / "raw"
    metadata_root = root / "metadata"
    raw_root.mkdir(parents=True, exist_ok=True)
    metadata_root.mkdir(parents=True, exist_ok=True)
    records = []
    for bgs_id in normalized:
        attributes = metadata[bgs_id]
        source_url = str(attributes.get("SCAN_URL") or SCAN_URL.format(bgs_id=bgs_id))
        if not source_url.startswith("https://api.bgs.ac.uk/"):
            raise ValueError(f"BGS ID {bgs_id} is not a direct public API scan: {source_url}")
        destination = raw_root / f"bgs_{bgs_id}.pdf"
        if destination.exists():
            if not destination.read_bytes()[:5] == b"%PDF-":
                raise RuntimeError(f"existing BGS file is not a PDF: {destination}")
        else:
            payload = _get(source_url)
            if not payload.startswith(b"%PDF-"):
                raise RuntimeError(f"BGS ID {bgs_id} did not return a PDF")
            destination.write_bytes(payload)
        records.append(DatasetFile(
            dataset_id="bgs_opengeoscience_v001",
            source_record_id=str(bgs_id),
            source_url=source_url,
            local_path=str(destination),
            sha256=sha256_file(destination),
            size_bytes=destination.stat().st_size,
            media_type=mimetypes.guess_type(destination.name)[0] or "application/octet-stream",
            access_date=access_date,
            license_id="OGL-UK-3.0",
            redistribution="allowed_with_attribution_subject_to_source_terms",
            metadata=attributes,
        ))
    response_path = metadata_root / f"fixed_ids_{'_'.join(map(str, normalized))}.json"
    response_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = metadata_root / "manifest.jsonl"
    write_jsonl(records, manifest_path)
    return manifest_path
