"""Reproducible, metadata-only discovery of candidate borehole datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


DATACITE_API = "https://api.datacite.org/dois"
FIGSHARE_SEARCH_API = "https://api.figshare.com/v2/articles/search"
MENDELEY_SEARCH_API = "https://api.data.mendeley.com/datasets"
MENDELEY_FILES_API = "https://data.mendeley.com/public-api/datasets"
ZENODO_RECORD_API = "https://zenodo.org/api/records"
SURVEY_USER_AGENT = "GeoLogParser-Metadata-Survey/0.1 (+https://github.com/GeoLogParser)"
SURVEY_TOOL_VERSION = "open_metadata_survey_v001"

PHASE1_REVIEW_DISPOSITIONS = {"phase1_content_review_candidate"}
PHASE1_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


@dataclass(frozen=True)
class FetchResult:
    status: int | None
    headers: dict[str, str]
    body: bytes
    error: str | None = None


Fetcher = Callable[[str, str, Mapping[str, str], bytes | None, float], FetchResult]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _default_fetcher(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
    timeout: float,
) -> FetchResult:
    request_headers = {"User-Agent": SURVEY_USER_AGENT, **dict(headers)}
    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed public APIs/configured metadata URLs
            return FetchResult(
                status=response.status,
                headers={key.lower(): value for key, value in response.headers.items()},
                body=response.read(),
            )
    except HTTPError as exc:
        return FetchResult(
            status=exc.code,
            headers={key.lower(): value for key, value in exc.headers.items()},
            body=exc.read(),
            error=f"HTTP {exc.code}: {exc.reason}",
        )
    except (URLError, TimeoutError, OSError) as exc:
        return FetchResult(status=None, headers={}, body=b"", error=f"{type(exc).__name__}: {exc}")


def _require_identifier(value: Any, *, field: str) -> str:
    text = str(value or "")
    if not text or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for character in text):
        raise ValueError(f"{field} must contain only letters, digits, '_' or '-'")
    return text


def _request_specs(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for item in config.get("datacite_queries", []):
        query_id = _require_identifier(item.get("id"), field="datacite query id")
        page_size = int(item.get("page_size", 100))
        if not 1 <= page_size <= 1000:
            raise ValueError(f"invalid DataCite page_size for {query_id}")
        params = {
            "query": str(item["query"]),
            "page[size]": str(page_size),
            "page[number]": str(int(item.get("page_number", 1))),
        }
        specs.append({
            "id": f"datacite_query_{query_id}",
            "kind": "datacite_query",
            "method": "GET",
            "url": f"{DATACITE_API}?{urlencode(params)}",
            "headers": {"Accept": "application/vnd.api+json"},
            "body": None,
            "query_id": query_id,
            "query": str(item["query"]),
        })
    for item in config.get("datacite_dois", []):
        request_id = _require_identifier(item.get("id"), field="DataCite DOI request id")
        doi = str(item["doi"]).lower()
        specs.append({
            "id": f"datacite_doi_{request_id}",
            "kind": "datacite_doi",
            "method": "GET",
            "url": f"{DATACITE_API}/{quote(doi, safe='')}",
            "headers": {"Accept": "application/vnd.api+json"},
            "body": None,
            "doi": doi,
        })
    for item in config.get("mendeley_file_probes", []):
        request_id = _require_identifier(item.get("id"), field="Mendeley file probe id")
        dataset_id = _require_identifier(item.get("dataset_id"), field="Mendeley dataset id")
        version = int(item["version"])
        params = urlencode({"folder_id": "root", "version": str(version)})
        specs.append({
            "id": f"mendeley_files_{request_id}",
            "kind": "mendeley_files",
            "method": "GET",
            "url": f"{MENDELEY_FILES_API}/{dataset_id}/files?{params}",
            "headers": {"Accept": "application/vnd.mendeley-public-dataset.1+json"},
            "body": None,
            "doi": str(item["doi"]).lower(),
            "dataset_id": dataset_id,
            "version": version,
        })
    for item in config.get("repository_probes", []):
        request_id = _require_identifier(item.get("id"), field="repository probe id")
        provider = str(item["provider"])
        query = str(item.get("query", ""))
        if provider == "figshare_search":
            payload = _json_bytes({
                "search_for": query,
                "limit": int(item.get("limit", 10)),
                "order": "published_date",
                "order_direction": "desc",
            })
            method, url = "POST", FIGSHARE_SEARCH_API
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
        elif provider == "mendeley_search":
            params = urlencode({"query": query, "page": "0", "limit": str(int(item.get("limit", 10)))})
            payload = None
            method, url = "GET", f"{MENDELEY_SEARCH_API}?{params}"
            headers = {"Accept": "application/json"}
        elif provider == "zenodo_record":
            record_id = _require_identifier(item.get("record_id"), field="Zenodo record id")
            payload = None
            method, url = "GET", f"{ZENODO_RECORD_API}/{record_id}"
            headers = {"Accept": "application/json"}
        elif provider == "url_status":
            payload = None
            method, url = "GET", str(item["url"])
            headers = {"Accept": str(item.get("accept", "text/html,application/json"))}
        else:
            raise ValueError(f"unsupported repository probe provider: {provider}")
        specs.append({
            "id": f"repository_{request_id}",
            "kind": "repository_probe",
            "provider": provider,
            "method": method,
            "url": url,
            "headers": headers,
            "body": payload,
            "query": query or None,
        })
    identifiers = [item["id"] for item in specs]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("survey request ids must be unique")
    return specs


def _parse_json(result: FetchResult) -> Any | None:
    if not result.body:
        return None
    try:
        return json.loads(result.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _datacite_record(resource: Mapping[str, Any], query_id: str | None) -> dict[str, Any]:
    attributes = resource.get("attributes", {})
    titles = attributes.get("titles") or []
    descriptions = attributes.get("descriptions") or []
    rights = attributes.get("rightsList") or []
    record = {
        "doi": str(attributes.get("doi") or resource.get("id") or "").lower(),
        "title": str(titles[0].get("title", "")) if titles else "",
        "publisher": attributes.get("publisher"),
        "publication_year": attributes.get("publicationYear"),
        "language": attributes.get("language"),
        "resource_type": (attributes.get("types") or {}).get("resourceTypeGeneral"),
        "url": attributes.get("url"),
        "formats": attributes.get("formats") or [],
        "sizes": attributes.get("sizes") or [],
        "content_url": attributes.get("contentUrl"),
        "rights": rights,
        "rights_identifiers": sorted({
            str(item.get("rightsIdentifier"))
            for item in rights
            if item.get("rightsIdentifier")
        }),
        "descriptions": [str(item.get("description", "")) for item in descriptions],
        "query_ids": [query_id] if query_id else [],
    }
    return record


def _merge_record(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    target["query_ids"] = sorted(set(target.get("query_ids", [])) | set(incoming.get("query_ids", [])))
    for field in ("title", "publisher", "publication_year", "language", "resource_type", "url", "content_url"):
        if target.get(field) in (None, "", []):
            target[field] = incoming.get(field)
    for field in ("formats", "sizes", "rights_identifiers"):
        target[field] = sorted({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in target.get(field, []) + incoming.get(field, [])})
        target[field] = [json.loads(value) for value in target[field]]
    if not target.get("rights"):
        target["rights"] = incoming.get("rights", [])
    if not target.get("descriptions"):
        target["descriptions"] = incoming.get("descriptions", [])


def _file_inventory(spec: Mapping[str, Any], payload: Any, result: FetchResult) -> dict[str, Any]:
    files = payload if isinstance(payload, list) else []
    normalized = []
    for item in files:
        if not isinstance(item, Mapping):
            continue
        details = item.get("content_details") or {}
        normalized.append({
            "filename": item.get("filename"),
            "file_id": item.get("id"),
            "content_type": details.get("content_type"),
            "size_bytes": details.get("size", item.get("size")),
            "sha256": details.get("sha256_hash"),
            "status": item.get("status"),
        })
    content_types = sorted({str(item["content_type"]) for item in normalized if item.get("content_type")})
    return {
        "doi": spec["doi"],
        "dataset_id": spec["dataset_id"],
        "version": spec["version"],
        "http_status": result.status,
        "request_error": result.error,
        "file_count": len(normalized) if result.status == 200 and isinstance(payload, list) else None,
        "total_size_bytes": sum(int(item["size_bytes"]) for item in normalized if isinstance(item.get("size_bytes"), int)),
        "content_types": content_types,
        "files": normalized,
    }


def _artifact_manifest(root: Path, *, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    excluded = exclude or set()
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        rows.append({"path": relative, "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)})
    return rows


def _is_phase1_content_review_candidate(
    review: Mapping[str, Any],
    inventory: Mapping[str, Any] | None,
) -> bool:
    if review.get("disposition") not in PHASE1_REVIEW_DISPOSITIONS:
        return False
    if review.get("license_status") != "verified_open":
        return False
    if not inventory or inventory.get("http_status") != 200:
        return False
    return bool(PHASE1_CONTENT_TYPES & set(inventory.get("content_types", [])))


def verify_open_metadata_survey(root: Path) -> dict[str, Any]:
    """Verify the recursive artifact manifest and request/response links."""

    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {item["path"]: item for item in manifest["artifacts"]}
    actual_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if set(expected) != actual_paths:
        raise ValueError("survey artifact path set does not match manifest")
    for relative, evidence in expected.items():
        path = root / relative
        if path.stat().st_size != evidence["size_bytes"]:
            raise ValueError(f"survey artifact size mismatch: {relative}")
        if _sha256_file(path) != evidence["sha256"]:
            raise ValueError(f"survey artifact SHA256 mismatch: {relative}")
    request_files = sorted((root / "requests").glob("*.json"))
    for request_path in request_files:
        request = json.loads(request_path.read_text(encoding="utf-8"))
        relative = request["response_body_path"]
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError(f"unsafe response path in {request_path.name}")
        response_path = root / relative
        if response_path.stat().st_size != request["response_body_bytes"]:
            raise ValueError(f"request response size mismatch: {request['request_id']}")
        if _sha256_file(response_path) != request["response_body_sha256"]:
            raise ValueError(f"request response SHA256 mismatch: {request['request_id']}")
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if summary["request_count"] != len(request_files):
        raise ValueError("summary request count does not match request evidence")
    return {
        "survey_id": manifest["survey_id"],
        "manifest_sha256": _sha256_file(manifest_path),
        "artifact_count": len(expected),
        "request_count": len(request_files),
        "verified": True,
    }


def run_open_metadata_survey(
    config: Mapping[str, Any],
    destination: Path,
    *,
    timeout: float = 30.0,
    fetcher: Fetcher | None = None,
) -> dict[str, Any]:
    """Run a metadata-only survey and freeze all request/response evidence."""

    survey_id = _require_identifier(config.get("survey_id"), field="survey_id")
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite survey output: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fetch = fetcher or _default_fetcher
    specs = _request_specs(config)
    started_at = _utc_now()
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        raw_root = temporary / "raw"
        request_root = temporary / "requests"
        raw_root.mkdir()
        request_root.mkdir()
        request_rows: list[dict[str, Any]] = []
        records: dict[str, dict[str, Any]] = {}
        inventories: list[dict[str, Any]] = []
        query_counts: dict[str, dict[str, Any]] = {}
        for spec in specs:
            requested_at = _utc_now()
            effective_headers = {"User-Agent": SURVEY_USER_AGENT, **spec["headers"]}
            result = fetch(spec["method"], spec["url"], effective_headers, spec["body"], timeout)
            completed_at = _utc_now()
            raw_relative = f"raw/{spec['id']}.body"
            raw_path = temporary / raw_relative
            raw_path.write_bytes(result.body)
            payload = _parse_json(result)
            request_evidence = {
                "request_id": spec["id"],
                "kind": spec["kind"],
                "provider": spec.get("provider"),
                "method": spec["method"],
                "url": spec["url"],
                "request_headers": effective_headers,
                "request_body_sha256": _sha256_bytes(spec["body"]) if spec["body"] is not None else None,
                "requested_at_utc": requested_at,
                "completed_at_utc": completed_at,
                "http_status": result.status,
                "response_headers": result.headers,
                "response_body_path": raw_relative,
                "response_body_bytes": len(result.body),
                "response_body_sha256": _sha256_bytes(result.body),
                "response_is_json": payload is not None,
                "error": result.error,
            }
            evidence_path = request_root / f"{spec['id']}.json"
            evidence_path.write_bytes(_json_bytes(request_evidence))
            request_rows.append(request_evidence)
            if spec["kind"] == "datacite_query" and isinstance(payload, Mapping):
                resources = payload.get("data") if isinstance(payload.get("data"), list) else []
                source_total = (payload.get("meta") or {}).get("total")
                query_counts[spec["query_id"]] = {
                    "query": spec["query"],
                    "http_status": result.status,
                    "source_reported_total": source_total,
                    "records_returned": len(resources),
                }
                for resource in resources:
                    if not isinstance(resource, Mapping):
                        continue
                    record = _datacite_record(resource, spec["query_id"])
                    if not record["doi"]:
                        continue
                    if record["doi"] in records:
                        _merge_record(records[record["doi"]], record)
                    else:
                        records[record["doi"]] = record
            elif spec["kind"] == "datacite_doi" and isinstance(payload, Mapping):
                resource = payload.get("data")
                if isinstance(resource, Mapping):
                    record = _datacite_record(resource, None)
                    if record["doi"] in records:
                        _merge_record(records[record["doi"]], record)
                    elif record["doi"]:
                        records[record["doi"]] = record
            elif spec["kind"] == "mendeley_files":
                inventories.append(_file_inventory(spec, payload, result))

        record_rows = sorted(records.values(), key=lambda item: item["doi"])
        reviews = {str(item["doi"]).lower(): dict(item) for item in config.get("candidate_reviews", [])}
        reviewed_rows = []
        for doi, review in sorted(reviews.items()):
            record = records.get(doi)
            inventory = next((item for item in inventories if item["doi"] == doi), None)
            reviewed_rows.append({
                "doi": doi,
                "metadata_found": record is not None,
                "metadata": record,
                "review": review,
                "file_inventory": inventory,
                "phase1_content_review_candidate": _is_phase1_content_review_candidate(review, inventory),
                "benchmark_eligible": False,
            })

        (temporary / "records.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in record_rows),
            encoding="utf-8",
        )
        (temporary / "reviewed_candidates.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in reviewed_rows),
            encoding="utf-8",
        )
        (temporary / "file_inventories.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in sorted(inventories, key=lambda row: row["doi"])),
            encoding="utf-8",
        )
        failed_requests = [item["request_id"] for item in request_rows if item["http_status"] != 200]
        summary = {
            "survey_id": survey_id,
            "survey_tool_version": SURVEY_TOOL_VERSION,
            "evidence_class": "metadata_discovery_not_dataset_acquisition",
            "started_at_utc": started_at,
            "completed_at_utc": _utc_now(),
            "request_count": len(request_rows),
            "successful_request_count": len(request_rows) - len(failed_requests),
            "failed_request_count": len(failed_requests),
            "failed_request_ids": failed_requests,
            "datacite_queries": query_counts,
            "unique_datacite_records_returned": len(record_rows),
            "curated_candidate_count": len(reviewed_rows),
            "candidate_review_provenance": "automated_project_agent_metadata_triage",
            "phase1_content_review_candidate_count": sum(
                bool(item["phase1_content_review_candidate"]) for item in reviewed_rows
            ),
            "benchmark_eligible_candidate_count": 0,
            "mendeley_file_inventory_count": len(inventories),
            "policy_assertions": {
                "search_hit_is_dataset_count": False,
                "metadata_rights_is_embedded_content_clearance": False,
                "file_inventory_is_download": False,
                "content_review_candidate_requires_open_license_and_pdf_jpg_or_png_inventory": True,
                "metadata_survey_can_declare_benchmark_eligibility": False,
            },
        }
        (temporary / "summary.json").write_bytes(_json_bytes(summary))
        config_snapshot = json.loads(json.dumps(config, ensure_ascii=False))
        (temporary / "config_snapshot.json").write_bytes(_json_bytes(config_snapshot))
        manifest = {
            "survey_id": survey_id,
            "generated_at_utc": _utc_now(),
            "artifacts": _artifact_manifest(temporary, exclude={"manifest.json"}),
        }
        (temporary / "manifest.json").write_bytes(_json_bytes(manifest))
        os.replace(temporary, destination)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
