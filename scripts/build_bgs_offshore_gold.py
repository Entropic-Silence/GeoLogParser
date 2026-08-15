#!/usr/bin/env python3
"""Freeze paired BGS offshore borehole scans and authoritative intervals.

The source exposes scan metadata and geology intervals in separate ArcGIS
layers joined by ACTIVITY_ID.  Only interval rows explicitly described as
derived from a graphic log are retained.  The original IMAGE_URL host is
preserved; downloads use the currently reachable BGS-qualified host alias.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse, urlunparse

import requests


ROOT = Path(__file__).resolve().parents[1]
SERVICE = (
    "https://map.bgs.ac.uk/arcgis/rest/services/"
    "GeoIndex_Offshore/offshore_data/MapServer"
)
DEFAULT_DATASET_ROOT = Path(
    "/data/GeoLogParser/datasets/public/bgs_offshore_paired_v001"
)
DEFAULT_MANIFEST = ROOT / "datasets/manifests/bgs_offshore_gold_v001.jsonl"
DEFAULT_SPLIT = ROOT / "datasets/splits/bgs_offshore_gold_split_v001.json"
ACTIVITY_FIELDS = ",".join(
    [
        "ACTIVITY_ID", "SAMPLE_NAME", "SAMPLE_ALIAS", "DGSQ", "NUM", "CRUISE",
        "SHIP", "SOURCE_TITLE", "CLIENT", "CONTRACTOR", "EQUIPMENT_START_DATE",
        "EPSG_CODE", "EPSG", "X", "Y", "X_WGS84", "Y_WGS84", "DEPTH_UNITS",
        "WATER_DEPTH", "DEPTH_DATUM", "TERMINAL_DEPTH", "GEOL_SUMMARY",
        "IMAGE_URL", "CONFIDENTIALITY", "ACCESSUSE_RESTRIC", "TERMS_OF_USE",
        "TERMS_OF_USE_URL",
    ]
)
GEOLOGY_FIELDS = ",".join(
    [
        "GEOLOGICAL_DATA_ID", "ACTIVITY_ID", "SAMPLE_NAME", "UNIT_DEPTH_TOP",
        "UNIT_DEPTH_BASE", "UNIT_LENGTH", "ROCK_CLASS_MAIN", "ROCK_CLASS_MINOR",
        "CGI_SIMPLE_LITHOLOGY", "GEOL_DESC", "INTERP_SOURCE", "DEPTH_UNITS",
        "TERMS_OF_USE", "TERMS_OF_USE_URL",
    ]
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def query_all(
    session: requests.Session, layer: int, where: str, fields: str,
) -> list[dict]:
    output: list[dict] = []
    offset = 0
    while True:
        response = session.get(
            f"{SERVICE}/{layer}/query",
            params={
                "f": "json",
                "where": where,
                "outFields": fields,
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": 2000,
                "orderByFields": "ACTIVITY_ID",
            },
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(payload["error"])
        features = [item["attributes"] for item in payload.get("features", [])]
        output.extend(features)
        if len(features) < 2000:
            break
        offset += len(features)
    return output


def resolved_download_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.netloc.lower() == "marinedata.ac.uk":
        parsed = parsed._replace(netloc="marinedata.bgs.ac.uk")
    return urlunparse(parsed)


def safe_filename(source_url: str, activity_id: int) -> str:
    name = Path(urlparse(source_url).path).name
    if not name.lower().endswith(".pdf"):
        name = f"{activity_id}.pdf"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def download_pdf(session: requests.Session, url: str, target: Path) -> None:
    if target.is_file() and target.stat().st_size > 4:
        if target.read_bytes()[:4] == b"%PDF":
            return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    try:
        with session.get(url, stream=True, timeout=(30, 300)) as response:
            response.raise_for_status()
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        if temporary.read_bytes()[:4] != b"%PDF":
            raise ValueError("download did not produce a PDF")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def remote_content_length(session: requests.Session, url: str) -> int | None:
    response = session.head(url, allow_redirects=True, timeout=60)
    response.raise_for_status()
    value = response.headers.get("Content-Length")
    return int(value) if value and value.isdigit() else None


def pdf_page_count(path: Path) -> int:
    completed = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True, check=True,
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if not match:
        raise ValueError("pdfinfo did not report a page count")
    return int(match.group(1))


def composite_log_pages(path: Path, page_count: int) -> tuple[list[int], str]:
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    pages = completed.stdout.split("\f")
    output = [
        index
        for index, text in enumerate(pages[:page_count], start=1)
        if "BH_COMP_LOG" in text.upper() or "COMPOSITE LOG" in text.upper()
    ]
    if output:
        return output, "native_text_marker"

    # Older image-only source groups expose no searchable marker.  A low-DPI
    # OCR pass is used only to locate candidate log pages; interval extraction
    # remains a separate, higher-resolution reference-blind stage.
    tesseract = shutil.which("tesseract")
    pdftoppm = shutil.which("pdftoppm")
    if tesseract is None or pdftoppm is None:
        return [], "no_page_locator_runtime"
    located: list[int] = []
    with tempfile.TemporaryDirectory(prefix="geologparser-bgs-page-locator-") as temporary:
        root = Path(temporary)
        completed = subprocess.run(
            [pdftoppm, "-jpeg", "-r", "120", str(path), str(root / "page")],
            capture_output=True, text=True, check=False,
        )
        if completed.returncode != 0:
            return [], "ocr_page_locator_render_failed"
        for index, image in enumerate(sorted(root.glob("page-*.jpg")), start=1):
            result = subprocess.run(
                [tesseract, str(image), "stdout", "-l", "eng", "--psm", "11"],
                capture_output=True, text=True, check=False,
            )
            text = result.stdout.upper()
            direct = "COMPOSITE LOG" in text or "BH_COMP_LOG" in text
            semantic = (
                "DEPTH" in text
                and ("DESCRIPTION" in text or "LITHOLOGY" in text)
                and ("BOREHOLE" in text or "SAMPLE" in text)
            )
            if direct or semantic:
                located.append(index)
    return located, "low_dpi_ocr_semantic_locator"


def deduplicate_intervals(rows: list[dict]) -> list[dict]:
    output: list[dict] = []
    seen: set[tuple] = set()
    for row in sorted(
        rows,
        key=lambda item: (
            float(item["UNIT_DEPTH_TOP"]), float(item["UNIT_DEPTH_BASE"]),
            int(item["GEOLOGICAL_DATA_ID"]),
        ),
    ):
        key = (
            round(float(row["UNIT_DEPTH_TOP"]), 6),
            round(float(row["UNIT_DEPTH_BASE"]), 6),
            str(row.get("GEOL_DESC") or ""),
        )
        if key not in seen:
            seen.add(key)
            output.append(row)
    return output


def eligible_intervals(rows: list[dict], minimum: int, maximum: int) -> list[dict] | None:
    selected = deduplicate_intervals(
        [
            row for row in rows
            if "graphic log" in str(row.get("INTERP_SOURCE") or "").lower()
        ]
    )
    if not minimum <= len(selected) <= maximum:
        return None
    if any(
        float(row["UNIT_DEPTH_TOP"]) < 0
        or float(row["UNIT_DEPTH_BASE"]) <= float(row["UNIT_DEPTH_TOP"])
        for row in selected
    ):
        return None
    if any(
        float(selected[index]["UNIT_DEPTH_TOP"])
        < float(selected[index - 1]["UNIT_DEPTH_BASE"]) - 0.01
        for index in range(1, len(selected))
    ):
        return None
    adjacent = sum(
        abs(
            float(selected[index]["UNIT_DEPTH_TOP"])
            - float(selected[index - 1]["UNIT_DEPTH_BASE"])
        ) <= 0.01
        for index in range(1, len(selected))
    )
    continuity = adjacent / max(1, len(selected) - 1)
    return selected if continuity >= 0.95 else None


def candidate_order(candidates: list[tuple[dict, list[dict]]]) -> list[tuple[dict, list[dict]]]:
    by_source: dict[str, list[tuple[dict, list[dict]]]] = defaultdict(list)
    for item in candidates:
        source = str(item[0].get("SOURCE_TITLE") or "UNKNOWN_SOURCE")
        by_source[source].append(item)
    for values in by_source.values():
        values.sort(key=lambda item: (abs(len(item[1]) - 15), int(item[0]["ACTIVITY_ID"])))
    output: list[tuple[dict, list[dict]]] = []
    depth = 0
    while True:
        added = False
        for source in sorted(by_source):
            values = by_source[source]
            if depth < len(values):
                output.append(values[depth])
                added = True
        if not added:
            return output
        depth += 1


def as_manifest_row(
    activity: dict, intervals: list[dict], pdf: Path, pages: int,
    evaluation_pages: list[int], evaluation_page_locator: str,
    source_url: str, download_url: str,
) -> dict:
    record_id = f"BGS_OFFSHORE_{activity['ACTIVITY_ID']}"
    return {
        "record_id": record_id,
        "activity_id": int(activity["ACTIVITY_ID"]),
        "borehole_id": activity["SAMPLE_NAME"],
        "sample_alias": activity.get("SAMPLE_ALIAS"),
        "source_title": activity.get("SOURCE_TITLE"),
        "cruise": activity.get("CRUISE"),
        "ship": activity.get("SHIP"),
        "client": activity.get("CLIENT"),
        "contractor": activity.get("CONTRACTOR"),
        "equipment_start_date_epoch_ms": activity.get("EQUIPMENT_START_DATE"),
        "x_wgs84": activity.get("X_WGS84"),
        "y_wgs84": activity.get("Y_WGS84"),
        "source_epsg": activity.get("EPSG"),
        "source_x": activity.get("X"),
        "source_y": activity.get("Y"),
        "water_depth_m": activity.get("WATER_DEPTH"),
        "terminal_depth_m": activity.get("TERMINAL_DEPTH"),
        "depth_datum": activity.get("DEPTH_DATUM"),
        "geological_summary": activity.get("GEOL_SUMMARY"),
        "pdf_path": str(pdf),
        "pdf_sha256": sha256(pdf),
        "pdf_pages": pages,
        "evaluation_pages": evaluation_pages,
        "evaluation_page_locator": evaluation_page_locator,
        "source_image_url": source_url,
        "resolved_download_url": download_url,
        "source_service": SERVICE,
        "source_activity_layer": 6,
        "source_geology_layer": 7,
        "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "reference_type": "BGS_official_geology_interpretation_derived_from_graphic_log",
        "project_human_reviewed": False,
        "source_human_transcribed": None,
        "license": "UK-Open-Government-Licence-3.0 per ArcGIS record",
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "rights_conflict_note": (
            "ArcGIS record states OGL 3.0; scanned PDF footer contains legacy "
            "all-rights-reserved wording. Original PDF remains local pending review."
        ),
        "confidentiality": activity.get("CONFIDENTIALITY"),
        "access_use_restriction": activity.get("ACCESSUSE_RESTRIC"),
        "terms_of_use": activity.get("TERMS_OF_USE"),
        "terms_of_use_url": activity.get("TERMS_OF_USE_URL"),
        "unit": "m_below_seabed",
        "interval_count": len(intervals),
        "intervals": [
            {
                "interval_id": f"{record_id}_I{index:03d}",
                "geological_data_id": int(item["GEOLOGICAL_DATA_ID"]),
                "top_depth_m": float(item["UNIT_DEPTH_TOP"]),
                "bottom_depth_m": float(item["UNIT_DEPTH_BASE"]),
                "thickness_m": float(item["UNIT_LENGTH"]),
                "lithology_raw": item.get("ROCK_CLASS_MAIN"),
                "lithology_minor_raw": item.get("ROCK_CLASS_MINOR"),
                "lithology_normalized": item.get("CGI_SIMPLE_LITHOLOGY"),
                "description_raw": item.get("GEOL_DESC"),
                "interpretation_source": item.get("INTERP_SOURCE"),
            }
            for index, item in enumerate(intervals, start=1)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    parser.add_argument("--target-documents", type=int, default=26)
    parser.add_argument("--minimum-intervals", type=int, default=5)
    parser.add_argument("--maximum-intervals", type=int, default=60)
    parser.add_argument("--max-pdf-bytes", type=int, default=30_000_000)
    parser.add_argument(
        "--exclude-manifest", type=Path, action="append", default=[],
        help="Exclude every record and SOURCE_TITLE already present in an earlier freeze.",
    )
    parser.add_argument("--dataset-version", default="bgs_offshore_paired_v001")
    parser.add_argument(
        "--split-version", default="bgs_offshore_gold_split_v001_source_group_disjoint_external",
    )
    args = parser.parse_args()

    excluded_record_ids: set[str] = set()
    excluded_source_titles: set[str] = set()
    excluded_manifest_hashes: list[dict[str, str]] = []
    for path in args.exclude_manifest:
        rows = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        excluded_record_ids.update(str(row["record_id"]) for row in rows)
        excluded_source_titles.update(
            str(row.get("source_title") or "UNKNOWN_SOURCE") for row in rows
        )
        excluded_manifest_hashes.append({"path": str(path), "sha256": sha256(path)})

    session = requests.Session()
    session.headers["User-Agent"] = "GeoLogParser-research/1.0"
    activities = query_all(session, 6, "IMAGE_URL IS NOT NULL", ACTIVITY_FIELDS)
    geology = query_all(
        session, 7,
        "UNIT_DEPTH_TOP IS NOT NULL AND UNIT_DEPTH_BASE IS NOT NULL",
        GEOLOGY_FIELDS,
    )
    activity_ids = {int(row["ACTIVITY_ID"]) for row in activities}
    by_activity: dict[int, list[dict]] = defaultdict(list)
    for row in geology:
        activity_id = int(row["ACTIVITY_ID"])
        if activity_id in activity_ids:
            by_activity[activity_id].append(row)

    candidates: list[tuple[dict, list[dict]]] = []
    for activity in activities:
        if str(activity.get("DEPTH_UNITS") or "").lower() != "metres":
            continue
        if "open government licence" not in str(activity.get("TERMS_OF_USE") or "").lower():
            continue
        intervals = eligible_intervals(
            by_activity[int(activity["ACTIVITY_ID"])],
            args.minimum_intervals,
            args.maximum_intervals,
        )
        if intervals is not None:
            candidates.append((activity, intervals))

    rows: list[dict] = []
    failures: list[dict] = []
    used_sources: set[str] = set()
    for activity, intervals in candidate_order(candidates):
        if len(rows) >= args.target_documents:
            break
        source_title = str(activity.get("SOURCE_TITLE") or "UNKNOWN_SOURCE")
        record_id = f"BGS_OFFSHORE_{activity['ACTIVITY_ID']}"
        if source_title in excluded_source_titles or record_id in excluded_record_ids:
            continue
        if source_title in used_sources:
            continue
        source_url = str(activity["IMAGE_URL"])
        download_url = resolved_download_url(source_url)
        pdf = args.dataset_root / "pdfs" / safe_filename(
            source_url, int(activity["ACTIVITY_ID"]),
        )
        try:
            content_length = remote_content_length(session, download_url)
            if content_length is not None and content_length > args.max_pdf_bytes:
                pdf.with_suffix(pdf.suffix + ".part").unlink(missing_ok=True)
                raise ValueError(
                    f"remote PDF size {content_length} exceeds max_pdf_bytes "
                    f"{args.max_pdf_bytes}"
                )
            download_pdf(session, download_url, pdf)
            page_count = pdf_page_count(pdf)
            evaluation_pages, page_locator = composite_log_pages(pdf, page_count)
            if not evaluation_pages:
                raise ValueError("no BH_COMP_LOG composite page found")
            row = as_manifest_row(
                activity, intervals, pdf, page_count, evaluation_pages, page_locator,
                source_url, download_url,
            )
        except Exception as exc:  # pragma: no cover - network/data dependent
            failures.append({
                "activity_id": int(activity["ACTIVITY_ID"]),
                "source_title": source_title,
                "source_url": source_url,
                "resolved_download_url": download_url,
                "remote_content_length": content_length,
                "error": str(exc),
            })
            print(f"rejected {activity['ACTIVITY_ID']}: {exc}", flush=True)
            continue
        rows.append(row)
        used_sources.add(source_title)
        print(
            f"selected {row['record_id']}: intervals={row['interval_count']} "
            f"pages={row['pdf_pages']} composite={row['evaluation_pages']}",
            flush=True,
        )

    if len(rows) != args.target_documents:
        raise RuntimeError(
            f"selected {len(rows)} documents, expected {args.target_documents}; "
            f"source_groups={len(used_sources)} failures={len(failures)}"
        )

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    split = {
        "split_version": args.split_version,
        "dataset_manifest": str(args.manifest.resolve().relative_to(ROOT)),
        "dataset_manifest_sha256": sha256(args.manifest),
        "development": [],
        "test": sorted(row["record_id"] for row in rows),
        "development_documents": 0,
        "test_documents": len(rows),
        "source_group_count": len(used_sources),
        "excluded_record_count": len(excluded_record_ids),
        "excluded_source_group_count": len(excluded_source_titles),
        "excluded_manifests": excluded_manifest_hashes,
        "selection_policy": (
            "one deterministic eligible record per SOURCE_TITLE, prioritizing "
            "interval count nearest 15; all records are external to method development"
        ),
    }
    args.split.parent.mkdir(parents=True, exist_ok=True)
    args.split.write_text(
        json.dumps(split, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metadata = {
        "dataset_version": args.dataset_version,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "activity_query": {
            "service": SERVICE, "layer": 6, "where": "IMAGE_URL IS NOT NULL",
            "returned_records": len(activities),
        },
        "geology_query": {
            "service": SERVICE, "layer": 7,
            "where": "UNIT_DEPTH_TOP IS NOT NULL AND UNIT_DEPTH_BASE IS NOT NULL",
            "returned_records": len(geology),
        },
        "eligible_candidate_documents": len(candidates),
        "eligible_candidate_source_groups": len(
            {str(item[0].get("SOURCE_TITLE") or "UNKNOWN_SOURCE") for item in candidates}
        ),
        "selected_documents": len(rows),
        "selected_source_groups": len(used_sources),
        "selected_pdf_pages": sum(row["pdf_pages"] for row in rows),
        "selected_evaluation_pages": sum(len(row["evaluation_pages"]) for row in rows),
        "selected_intervals": sum(row["interval_count"] for row in rows),
        "excluded_record_count": len(excluded_record_ids),
        "excluded_source_group_count": len(excluded_source_titles),
        "excluded_manifests": excluded_manifest_hashes,
        "manifest": {"path": str(args.manifest), "sha256": sha256(args.manifest)},
        "split": {"path": str(args.split), "sha256": sha256(args.split)},
        "failed_or_rejected_downloads": failures,
        "ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "project_human_reviewed": False,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "rights_conflict_note": (
            "ArcGIS records state OGL 3.0 while scan footers may contain legacy "
            "copyright wording; public redistribution is not authorized by this build."
        ),
    }
    metadata_root = args.dataset_root / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    (metadata_root / "acquisition.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
