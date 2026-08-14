#!/usr/bin/env python3
"""Freeze a small public Swissgeol Thurgau PDF/database pairing pilot.

The acquisition deliberately limits reference labels to fields returned by the
official borehole database.  In particular, layer ``fromDepth``/``toDepth``
values are authoritative database references, not newly annotated image
labels.  Material descriptions and codelist semantics are outside this pilot.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_ROOT = "https://boreholes.swissgeol.ch/api/v2"
DATASET_VERSION = "swissgeol_thurgau_paired_v001"
FILTER_REQUEST = {
    "pageNumber": 1,
    "pageSize": 100,
    "orderBy": "name",
    "direction": "ASC",
    "hasProfiles": 1,
    "canton": ["Thurgau"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


class SwissgeolClient:
    """Small anonymous client for documented endpoints used by the public UI."""

    def __init__(self, api_root: str = API_ROOT, retries: int = 3) -> None:
        self.api_root = api_root.rstrip("/")
        self.retries = retries

    def _request(self, path: str, *, method: str = "GET", body: Any = None) -> bytes:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            f"{self.api_root}/{path.lstrip('/')}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "User-Agent": "GeoLogParser/0.0.1"},
        )
        error: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urlopen(request, timeout=60) as response:
                    return response.read()
            except (HTTPError, URLError, TimeoutError) as exc:
                error = exc
                if attempt + 1 < self.retries:
                    time.sleep(0.5 * (attempt + 1))
        assert error is not None
        raise error

    def json(self, path: str, *, method: str = "GET", body: Any = None) -> Any:
        return json.loads(self._request(path, method=method, body=body))

    def bytes(self, path: str) -> bytes:
        return self._request(path)


def primary_published_stratigraphy(detail: dict[str, Any]) -> dict[str, Any] | None:
    workflow = detail.get("workflow") or {}
    published = workflow.get("publishedTabs") or {}
    if workflow.get("status") != "Published" or not published.get("lithology"):
        return None
    stratigraphies = detail.get("stratigraphies") or []
    primary = [item for item in stratigraphies if item.get("isPrimary")]
    candidates = primary or stratigraphies
    for item in candidates:
        if item.get("boreholeId") == detail.get("id") and item.get("lithologies"):
            return item
    return None


def public_pdf_profile(detail: dict[str, Any]) -> dict[str, Any] | None:
    workflow = detail.get("workflow") or {}
    published = workflow.get("publishedTabs") or {}
    if workflow.get("status") != "Published" or not published.get("profiles"):
        return None
    profiles = [
        item
        for item in (detail.get("profiles") or [])
        if item.get("public") is True
        and item.get("type") == "application/pdf"
        and item.get("boreholeId") == detail.get("id")
    ]
    return sorted(profiles, key=lambda item: (item.get("id", 0), item.get("name", "")))[0] if profiles else None


def depth_reference(detail: dict[str, Any], stratigraphy: dict[str, Any]) -> dict[str, Any]:
    intervals = []
    for index, layer in enumerate(stratigraphy.get("lithologies") or [], 1):
        top = layer.get("fromDepth")
        bottom = layer.get("toDepth")
        if top is None or bottom is None:
            continue
        intervals.append(
            {
                "interval_id": f"{detail['id']}_I{index:03d}",
                "source_layer_id": layer.get("id"),
                "top_depth_m": float(top),
                "bottom_depth_m": float(bottom),
                "thickness_m": float(bottom) - float(top),
                "is_unconsolidated": layer.get("isUnconsolidated"),
            }
        )
    return {
        "reference_type": "official_database_derived_ground_truth",
        "reference_scope": ["borehole_metadata", "interval_boundaries"],
        "excluded_reference_scope": ["material_description", "lithology_text", "image_bbox"],
        "borehole": {
            "borehole_id": str(detail["id"]),
            "name": detail.get("name"),
            "project_name": detail.get("projectName"),
            "x_coordinate": detail.get("locationX"),
            "y_coordinate": detail.get("locationY"),
            "coordinate_system": "CH1903+/LV95",
            "collar_elevation_m": detail.get("elevationZ"),
            "final_depth_m": detail.get("totalDepth"),
            "canton": detail.get("canton"),
            "municipality": detail.get("municipality"),
        },
        "stratigraphy": {
            "stratigraphy_id": stratigraphy.get("id"),
            "name": stratigraphy.get("name"),
            "is_primary": stratigraphy.get("isPrimary"),
            "intervals": intervals,
        },
    }


def candidate_rows(
    client: SwissgeolClient,
    *,
    maximum_pages: int = 10,
    start_page: int = 1,
    canton: str = "Thurgau",
) -> tuple[list[dict[str, Any]], int]:
    if start_page < 1:
        raise ValueError("start_page must be >= 1")
    rows: list[dict[str, Any]] = []
    total_count = 0
    for page_number in range(start_page, start_page + maximum_pages):
        request = {**FILTER_REQUEST, "pageNumber": page_number, "canton": [canton]}
        response = client.json("borehole/filter", method="POST", body=request)
        total_count = int(response.get("totalCount", 0))
        page_rows = response.get("boreholes") or []
        rows.extend(page_rows)
        if page_number >= int(response.get("totalPages", 0)) or not page_rows:
            break
    return rows, total_count


def acquire(
    output_root: Path,
    *,
    limit: int,
    maximum_pages: int,
    client: SwissgeolClient,
    resume: bool = False,
    dataset_version: str = DATASET_VERSION,
    start_page: int = 1,
    canton: str = "Thurgau",
    record_prefix: str = "SWISSGEOL_TG",
    exclude_record_ids: set[str] | None = None,
) -> dict[str, Any]:
    if (output_root / "dataset.json").exists():
        raise FileExistsError(f"immutable dataset is already frozen: {output_root}")
    if output_root.exists() and any(output_root.iterdir()) and not resume:
        raise FileExistsError(f"incomplete dataset directory is not empty; pass --resume: {output_root}")
    pdf_dir = output_root / "pdf"
    reference_dir = output_root / "reference"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)

    rows, source_total = candidate_rows(
        client,
        maximum_pages=maximum_pages,
        start_page=start_page,
        canton=canton,
    )
    excluded_ids = exclude_record_ids or set()
    excluded_candidate_records = 0
    manifest: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        if len(manifest) >= limit:
            break
        borehole_id = int(row["id"])
        record_id = f"{record_prefix}_{borehole_id}"
        if record_id in excluded_ids:
            excluded_candidate_records += 1
            continue
        try:
            detail = client.json(f"borehole/{borehole_id}")
        except Exception as exc:  # acquisition must preserve per-record failures
            failures.append({"borehole_id": borehole_id, "stage": "detail", "error": repr(exc)})
            continue
        if detail.get("canton") != canton:
            continue
        stratigraphy = primary_published_stratigraphy(detail)
        profile = public_pdf_profile(detail)
        if stratigraphy is None or profile is None:
            continue
        reference = depth_reference(detail, stratigraphy)
        intervals = reference["stratigraphy"]["intervals"]
        if not intervals:
            continue
        pdf_path = pdf_dir / f"{record_id}.pdf"
        reference_path = reference_dir / f"{record_id}.json"
        if resume and pdf_path.exists():
            content = pdf_path.read_bytes()
        else:
            try:
                content = client.bytes(f"profile/download?profileId={profile['id']}")
            except Exception as exc:
                failures.append(
                    {
                        "borehole_id": borehole_id,
                        "profile_id": profile.get("id"),
                        "stage": "profile_download",
                        "error": repr(exc),
                    }
                )
                continue
        if not content.startswith(b"%PDF-"):
            failures.append(
                {
                    "borehole_id": borehole_id,
                    "profile_id": profile.get("id"),
                    "stage": "pdf_validation",
                    "error": "missing PDF magic",
                }
            )
            continue
        pdf_path.write_bytes(content)
        reference_path.write_text(
            json.dumps(reference, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest.append(
            {
                "record_id": record_id,
                "borehole_id": borehole_id,
                "profile_id": profile["id"],
                "stratigraphy_id": stratigraphy["id"],
                "profile_name": profile.get("name"),
                "profile_public": True,
                "workflow_status": "Published",
                "published_tabs": {"profiles": True, "lithology": True},
                "pairing_basis": "same_official_borehole_object",
                "reference_type": "official_database_derived_ground_truth",
                "interval_count": len(intervals),
                "pdf_path": str(pdf_path),
                "pdf_bytes": len(content),
                "pdf_sha256": sha256_bytes(content),
                "reference_path": str(reference_path),
                "reference_sha256": sha256_bytes(reference_path.read_bytes()),
                "source_endpoints": {
                    "detail": f"{API_ROOT}/borehole/{borehole_id}",
                    "profile_download": f"{API_ROOT}/profile/download?profileId={profile['id']}",
                },
                "manual_pairing_review": False,
                "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
            }
        )

    manifest_path = output_root / "manifest.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in manifest),
        encoding="utf-8",
    )
    failure_path = output_root / "failures.jsonl"
    failure_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in failures),
        encoding="utf-8",
    )
    summary = {
        "dataset_version": dataset_version,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": "swissgeol boreholes public anonymous interface",
        "api_root": API_ROOT,
        "source_filter": {
            **FILTER_REQUEST,
            "canton": [canton],
            "pageNumber": start_page,
            "maximum_pages": maximum_pages,
        },
        "source_filter_total_count": source_total,
        "candidate_rows_examined": len(rows),
        "excluded_candidate_records": excluded_candidate_records,
        "excluded_record_id_count": len(excluded_ids),
        "frozen_documents": len(manifest),
        "frozen_intervals": sum(item["interval_count"] for item in manifest),
        "failed_candidates": len(failures),
        "reference_type": "official_database_derived_ground_truth",
        "manual_pairing_review": False,
        "rights_review": "PENDING_MANUAL_PRE_SUBMISSION_REVIEW",
        "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "record_set_sha256": canonical_sha256(
            [{"record_id": item["record_id"], "pdf_sha256": item["pdf_sha256"], "reference_sha256": item["reference_sha256"]} for item in manifest]
        ),
    }
    (output_root / "dataset.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/data/GeoLogParser/datasets/public") / DATASET_VERSION,
    )
    parser.add_argument("--limit", type=int, default=32)
    parser.add_argument("--maximum-pages", type=int, default=10)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--canton", default="Thurgau")
    parser.add_argument("--record-prefix", default="SWISSGEOL_TG")
    parser.add_argument("--exclude-manifest", type=Path, action="append", default=[])
    parser.add_argument("--dataset-version", default=DATASET_VERSION)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    excluded_record_ids = set()
    for manifest_path in args.exclude_manifest:
        excluded_record_ids.update(
            json.loads(line)["record_id"]
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    summary = acquire(
        args.output_root,
        limit=args.limit,
        maximum_pages=args.maximum_pages,
        client=SwissgeolClient(),
        resume=args.resume,
        dataset_version=args.dataset_version,
        start_page=args.start_page,
        canton=args.canton,
        record_prefix=args.record_prefix,
        exclude_record_ids=excluded_record_ids,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
