"""Acquire public Mendeley files from a previously frozen file inventory."""

from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MENDELEY_DOWNLOAD_PREFIX = "https://data.mendeley.com/public-files/datasets/"
ACQUISITION_USER_AGENT = "GeoLogParser-Mendeley-Acquisition/0.1 (+https://github.com/GeoLogParser)"

Downloader = Callable[[str, float], bytes]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _default_downloader(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": ACQUISITION_USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - validated Mendeley URL prefix
            return response.read()
    except HTTPError as exc:
        raise RuntimeError(f"Mendeley download returned HTTP {exc.code}: {url}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Mendeley download failed: {url}: {exc}") from exc


def _safe_filename(value: Any) -> str:
    filename = str(value or "")
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError(f"unsafe Mendeley filename: {filename!r}")
    return filename


def _validated_inventory(path: Path, dataset_id: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("files")
    if not isinstance(payload, list) or not payload:
        raise ValueError("Mendeley inventory must be a non-empty JSON list or dataset object with files")
    rows: list[dict[str, Any]] = []
    filenames: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Mendeley inventory entries must be objects")
        details = item.get("content_details")
        if not isinstance(details, dict):
            raise ValueError("Mendeley inventory entry lacks content_details")
        filename = _safe_filename(item.get("filename"))
        if filename in filenames:
            raise ValueError(f"duplicate Mendeley filename: {filename}")
        filenames.add(filename)
        url = str(details.get("download_url") or "")
        expected_prefix = f"{MENDELEY_DOWNLOAD_PREFIX}{dataset_id}/files/"
        if not url.startswith(expected_prefix) or not url.endswith("/file_downloaded"):
            raise ValueError(f"unexpected Mendeley download URL for {filename}")
        sha256 = str(details.get("sha256_hash") or "").lower()
        if len(sha256) != 64 or any(character not in "0123456789abcdef" for character in sha256):
            raise ValueError(f"invalid SHA256 for {filename}")
        size = details.get("size", item.get("size"))
        if not isinstance(size, int) or size < 0:
            raise ValueError(f"invalid size for {filename}")
        rows.append({
            "filename": filename,
            "file_id": str(item.get("id") or ""),
            "content_type": details.get("content_type"),
            "size_bytes": size,
            "sha256": sha256,
            "download_url": url,
        })
    return rows


def acquire_frozen_mendeley_inventory(
    inventory_path: Path,
    destination: Path,
    *,
    dataset_id: str,
    dataset_doi: str,
    dataset_version: int,
    license_id: str,
    access_date: str | None = None,
    timeout: float = 300.0,
    downloader: Downloader | None = None,
    content_types: set[str] | None = None,
) -> dict[str, Any]:
    """Download and verify selected files from a frozen public inventory."""

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite acquired dataset: {destination}")
    inventory_rows = _validated_inventory(inventory_path, dataset_id)
    selected_types = sorted(content_types) if content_types is not None else None
    selected_rows = (
        [row for row in inventory_rows if row.get("content_type") in content_types]
        if content_types is not None
        else inventory_rows
    )
    if not selected_rows:
        raise ValueError("Mendeley inventory selection contains no files")
    acquisition_date = access_date or date.today().isoformat()
    download = downloader or _default_downloader
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        raw_root = temporary / "raw"
        metadata_root = temporary / "metadata"
        raw_root.mkdir()
        metadata_root.mkdir()
        acquired_rows = []
        for row in selected_rows:
            body = download(row["download_url"], timeout)
            if len(body) != row["size_bytes"]:
                raise ValueError(f"download size mismatch for {row['filename']}")
            actual_sha256 = _sha256_bytes(body)
            if actual_sha256 != row["sha256"]:
                raise ValueError(f"download SHA256 mismatch for {row['filename']}")
            target = raw_root / row["filename"]
            target.write_bytes(body)
            acquired_rows.append({
                **row,
                "local_path": str(destination / "raw" / row["filename"]),
                "access_date": acquisition_date,
                "license_id": license_id,
            })
        manifest_path = metadata_root / "manifest.jsonl"
        manifest_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in acquired_rows),
            encoding="utf-8",
        )
        evidence = {
            "acquisition_schema_version": "mendeley_frozen_inventory_v002",
            "dataset_id": dataset_id,
            "dataset_doi": dataset_doi.lower(),
            "dataset_version": dataset_version,
            "license_id": license_id,
            "access_date": acquisition_date,
            "source_inventory_path": str(inventory_path),
            "source_inventory_sha256": _sha256_file(inventory_path),
            "source_inventory_file_count": len(inventory_rows),
            "content_type_filter": selected_types,
            "selected_file_count": len(selected_rows),
            "file_count": len(acquired_rows),
            "total_size_bytes": sum(row["size_bytes"] for row in acquired_rows),
            "files": acquired_rows,
        }
        acquisition_path = metadata_root / "acquisition.json"
        acquisition_path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
        return {
            **evidence,
            "manifest_sha256": _sha256_file(destination / "metadata/manifest.jsonl"),
            "acquisition_sha256": _sha256_file(destination / "metadata/acquisition.json"),
        }
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_mendeley_acquisition(root: Path) -> dict[str, Any]:
    evidence_path = root / "metadata/acquisition.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    files = evidence.get("files")
    if not isinstance(files, list) or len(files) != evidence.get("file_count"):
        raise ValueError("Mendeley acquisition file count mismatch")
    seen: set[str] = set()
    for row in files:
        filename = _safe_filename(row.get("filename"))
        if filename in seen:
            raise ValueError(f"duplicate acquired filename: {filename}")
        seen.add(filename)
        path = root / "raw" / filename
        if path.stat().st_size != row["size_bytes"]:
            raise ValueError(f"acquired size mismatch: {filename}")
        if _sha256_file(path) != row["sha256"]:
            raise ValueError(f"acquired SHA256 mismatch: {filename}")
    actual_files = {path.name for path in (root / "raw").iterdir() if path.is_file()}
    if actual_files != seen:
        raise ValueError("acquired raw-file set does not match acquisition evidence")
    if sum(row["size_bytes"] for row in files) != evidence.get("total_size_bytes"):
        raise ValueError("Mendeley acquisition total size mismatch")
    return {
        "dataset_id": evidence["dataset_id"],
        "file_count": len(files),
        "total_size_bytes": evidence["total_size_bytes"],
        "acquisition_sha256": _sha256_file(evidence_path),
        "verified": True,
    }
