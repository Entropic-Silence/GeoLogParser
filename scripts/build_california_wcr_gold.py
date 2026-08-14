#!/usr/bin/env python3
"""Freeze a county-diverse California WCR manual-transcription benchmark."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WCR = Path("/data/GeoLogParser/datasets/public/usgs_california_wcr_v6_2025/raw/WCR_v6_2025.csv")
DEFAULT_LITHOLOGY = Path("/data/GeoLogParser/datasets/public/usgs_california_lithology_v3_2025/raw/Lithology_v3_2025.txt")
DEFAULT_DATASET_ROOT = Path("/data/GeoLogParser/datasets/public/california_wcr_gold_v001")
DEFAULT_MANIFEST = ROOT / "datasets/manifests/california_wcr_gold_v001.jsonl"
SELECTION_VERSION = "county_first_sha256_v001"
SELECTION_SEED = "GeoLogParser-California-WCR-Gold-v001"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_key(wcr_number: str) -> str:
    return hashlib.sha256(f"{SELECTION_SEED}|{wcr_number}".encode()).hexdigest()


def parse_pdf_pages(path: Path) -> int:
    completed = subprocess.run(
        ["pdfinfo", str(path)], capture_output=True, text=True, check=False
    )
    if completed.returncode:
        raise RuntimeError(f"pdfinfo failed for {path}: {completed.stderr.strip()}")
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"could not read page count for {path}")
    return int(match.group(1))


def fetch(url: str, *, attempts: int = 5) -> bytes:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "GeoLogParser research/0.1"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network dependent
            error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {error}")


def parse_box_preview(page_url: str) -> tuple[dict, str]:
    html = fetch(page_url).decode("utf-8", "replace")
    marker = "Box.prefetchedData = "
    start = html.find(marker)
    if start < 0:
        raise RuntimeError(f"Box preview metadata missing: {page_url}")
    payload, _ = json.JSONDecoder().raw_decode(html[start + len(marker):])
    metadata = payload["preview_metadata"]
    token = payload["preview_prefetch_token_map"][str(metadata["id"])]["read"]
    if metadata.get("extension", "").lower() != "pdf" or not metadata.get("is_download_available"):
        raise RuntimeError(f"public PDF download unavailable: {page_url}")
    return metadata, token


def download_box_pdf(page_url: str, target: Path) -> dict:
    metadata, token = parse_box_preview(page_url)
    request = urllib.request.Request(
        metadata["authenticated_download_url"],
        headers={"User-Agent": "GeoLogParser research/0.1", "Authorization": f"Bearer {token}"},
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".pdf.part")
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    if temporary.read_bytes()[:5] != b"%PDF-":
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"download was not a PDF: {page_url}")
    temporary.replace(target)
    return {
        "box_file_id": str(metadata["id"]),
        "box_file_version_id": str(metadata["file_version"]["id"]),
        "source_filename": metadata["name"],
        "source_sha1": metadata["sha1"],
        "declared_size_bytes": int(metadata["size"]),
    }


def load_wcr_metadata(path: Path) -> dict[str, dict]:
    output: dict[str, dict] = {}
    with path.open(encoding="cp1252", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("Lithology_Transcribed") == "Yes" and row.get("OSWCR_URL", "").startswith(
                "https://cadwr.app.box.com/"
            ):
                output[row["WCRNumber"]] = row
    return output


def load_intervals(path: Path) -> dict[str, list[dict]]:
    grouped: dict[str, dict[tuple[float, float, str], dict]] = defaultdict(dict)
    with path.open(encoding="cp1252", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                top = float(row["IntervalStartFt"])
                bottom = float(row["IntervalEndFt"])
            except (TypeError, ValueError):
                continue
            description = row.get("FreeForm", "").strip()
            if not (0 <= top < bottom <= 5000) or not description:
                continue
            key = (top, bottom, description)
            grouped[row["WCRNumber"]][key] = {
                "top_depth_ft": top,
                "bottom_depth_ft": bottom,
                "thickness_ft": bottom - top,
                "lithology_raw": description,
                "comments": row.get("Comments", "").strip(),
                "publish_date_group": row.get("PublishDate", "").strip(),
            }
    return {
        wcr: sorted(rows.values(), key=lambda item: (item["top_depth_ft"], item["bottom_depth_ft"], item["lithology_raw"]))
        for wcr, rows in grouped.items()
    }


def candidate_is_clean(intervals: list[dict]) -> bool:
    if not 5 <= len(intervals) <= 60:
        return False
    if any(item["comments"] for item in intervals):
        return False
    adjacent = list(zip(intervals, intervals[1:]))
    continuity = sum(abs(left["bottom_depth_ft"] - right["top_depth_ft"]) <= 0.01 for left, right in adjacent)
    return not adjacent or continuity / len(adjacent) >= 0.99


def build_candidate_order(metadata: dict[str, dict], intervals: dict[str, list[dict]]) -> list[str]:
    candidates = [wcr for wcr, rows in intervals.items() if wcr in metadata and candidate_is_clean(rows)]
    by_county: dict[str, list[str]] = defaultdict(list)
    for wcr in candidates:
        by_county[metadata[wcr]["County"]].append(wcr)
    for county in by_county:
        by_county[county].sort(key=stable_key)
    county_first = [by_county[county][0] for county in sorted(by_county)]
    remaining = sorted(set(candidates) - set(county_first), key=stable_key)
    return county_first + remaining


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wcr", type=Path, default=DEFAULT_WCR)
    parser.add_argument("--lithology", type=Path, default=DEFAULT_LITHOLOGY)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--target-documents", type=int, default=60)
    args = parser.parse_args()

    metadata = load_wcr_metadata(args.wcr)
    intervals = load_intervals(args.lithology)
    order = build_candidate_order(metadata, intervals)
    pdf_root = args.dataset_root / "pdfs"
    rows: list[dict] = []
    failures: list[dict] = []
    selected_counties: set[str] = set()
    for wcr in order:
        if len(rows) >= args.target_documents:
            break
        source = metadata[wcr]
        target = pdf_root / f"{wcr}.pdf"
        try:
            box = download_box_pdf(source["OSWCR_URL"], target) if not target.is_file() else {}
            pages = parse_pdf_pages(target)
        except Exception as exc:  # pragma: no cover - network dependent
            failures.append({"wcr_number": wcr, "source_url": source["OSWCR_URL"], "error": str(exc)})
            continue
        if not box:
            box = {
                "box_file_id": source["OSWCR_URL"].rstrip("/").split("/")[-1],
                "box_file_version_id": None,
                "source_filename": None,
                "source_sha1": None,
                "declared_size_bytes": target.stat().st_size,
            }
        row = {
            "record_id": wcr,
            "borehole_id": wcr,
            "county": source["County"],
            "mtrs": source["MTRS"],
            "legacy_log_number": source["LegacyLogNo"],
            "pdf_path": str(target),
            "pdf_sha256": file_sha256(target),
            "pdf_pages": pages,
            "source_url": source["OSWCR_URL"],
            "source_filename": box["source_filename"],
            "box_file_id": box["box_file_id"],
            "box_file_version_id": box["box_file_version_id"],
            "box_source_sha1": box["source_sha1"],
            "ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
            "source_human_transcribed": True,
            "source_quality_controlled": True,
            "project_human_reviewed": False,
            "reference_type": "USGS_verbatim_manual_WCR_interval_transcription",
            "reference_doi": "10.5066/P9M85U0T",
            "reference_version": "3.0_July_2025",
            "license": "CC0-1.0",
            "unit": "ft_bls",
            "hole_depth_ft": source["HoleDepth"] or None,
            "completed_depth_ft": source["CompletedDepth"] or None,
            "generalized_lithology": source["GeneralizedLithology"] or None,
            "publication_groups": sorted({item["publish_date_group"] for item in intervals[wcr]}),
            "interval_count": len(intervals[wcr]),
            "intervals": [
                {"interval_id": f"{wcr}_I{index:03d}", **item}
                for index, item in enumerate(intervals[wcr], start=1)
            ],
        }
        rows.append(row)
        selected_counties.add(source["County"])
        print(f"selected {wcr}: county={source['County']} intervals={len(intervals[wcr])} pages={pages}")

    if len(rows) != args.target_documents:
        raise RuntimeError(f"selected {len(rows)} documents, expected {args.target_documents}; failures={len(failures)}")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
    )
    acquisition = {
        "dataset_version": "california_wcr_gold_v001",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "selection_version": SELECTION_VERSION,
        "selection_seed": SELECTION_SEED,
        "source_release": {
            "title": "Compilation of lithologic data from selected well completion reports submitted to the California Department of Water Resources (ver. 3.0, July 2025)",
            "doi": "10.5066/P9M85U0T",
            "sciencebase_item": "632b1c93d34e71c6d67bc0bc",
            "license": "CC0-1.0",
            "manual_transcription_and_qc_evidence": "LithologyDR_2025_metadata.xml process steps and attribute accuracy report",
        },
        "link_release": {
            "title": "Attributed California Water Supply Well Completion Report Data for Selected Areas (ver. 6.0, December 2025)",
            "doi": "10.5066/P93ICKAF",
            "sciencebase_item": "64958d73d34ef77fcb01dc8f",
            "license": "CC0-1.0",
        },
        "source_files": {
            str(args.wcr): {"sha256": file_sha256(args.wcr), "size_bytes": args.wcr.stat().st_size},
            str(args.lithology): {"sha256": file_sha256(args.lithology), "size_bytes": args.lithology.stat().st_size},
        },
        "manifest": {"path": str(args.manifest), "sha256": file_sha256(args.manifest)},
        "selected_documents": len(rows),
        "selected_intervals": sum(row["interval_count"] for row in rows),
        "selected_counties": len(selected_counties),
        "county_names": sorted(selected_counties),
        "failed_downloads_before_target": failures,
        "selection_filters": {
            "box_public_pdf_link_required": True,
            "unique_intervals_after_exact_deduplication": "5..60",
            "interval_comments": "empty",
            "adjacent_boundary_continuity_rate": ">=0.99",
            "county_first": True,
            "remaining_order": "seeded_sha256",
        },
    }
    metadata_root = args.dataset_root / "metadata"
    metadata_root.mkdir(parents=True, exist_ok=True)
    (metadata_root / "acquisition.json").write_text(
        json.dumps(acquisition, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: acquisition[k] for k in ["selected_documents", "selected_intervals", "selected_counties", "manifest"]}, indent=2))


if __name__ == "__main__":
    main()
