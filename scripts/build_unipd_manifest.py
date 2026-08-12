#!/usr/bin/env python3
"""Build a fixed manifest for the acquired University of Padova log PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.pdf import detect_pdf


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("/data/GeoLogParser/datasets/public/unipd_levee_geotech_v001"))
    arguments = parser.parse_args()
    archive = arguments.dataset_root / "raw/RAW_DATA.zip"
    expected_md5 = "030f545f07da0abcb06ca4ead715bf9c"
    if digest(archive, "md5") != expected_md5:
        raise ValueError("University of Padova archive MD5 does not match repository record")
    rows = []
    for path in sorted((arguments.dataset_root / "documents").glob("*.pdf")):
        detection = detect_pdf(path)
        rows.append({
            "source_record_id": path.stem,
            "local_path": str(path),
            "sha256": digest(path),
            "page_count": len(detection.pages),
            "document_type": detection.document_type,
            "page_classifications": [page.classification for page in detection.pages],
            "language": "English",
            "source_dataset_doi": "10.25430/researchdata.cab.unipd.it.00001663",
            "license": "CC-BY-4.0",
            "redistribution": "allowed_with_attribution",
            "annotation_status": "unannotated",
        })
    metadata = arguments.dataset_root / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    manifest = metadata / "manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    acquisition = {
        "dataset_id": "unipd_levee_geotechnical_logs_v001",
        "doi": "10.25430/researchdata.cab.unipd.it.00001663",
        "repository_record_url": "https://researchdata.cab.unipd.it/id/eprint/1663",
        "repository_json_url": "https://researchdata.cab.unipd.it/cgi/export/eprint/1663/JSON/researchdata-eprint-1663.js",
        "file_url": "https://researchdata.cab.unipd.it/id/file/14335",
        "download_date": "2026-08-12",
        "file_license": "CC-BY-4.0",
        "archive_size_bytes": archive.stat().st_size,
        "archive_md5": digest(archive, "md5"),
        "archive_sha256": digest(archive),
        "documents": len(rows),
        "pages": sum(row["page_count"] for row in rows),
        "notes": "Borehole PDF subset extracted without modifying source archive; no manual GT yet.",
    }
    (metadata / "acquisition.json").write_text(json.dumps(acquisition, indent=2) + "\n", encoding="utf-8")
    print(manifest)


if __name__ == "__main__":
    main()
