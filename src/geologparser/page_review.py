"""Human content/privacy review for rendered PDF pages and standalone images."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
from typing import Any, Iterable, Mapping

import pymupdf

from geologparser.datasets.manifest import sha256_file


CHECK_NAMES = (
    "organization_or_project",
    "person_or_signature",
    "contact_or_address",
    "coordinates_or_sensitive_location",
    "stamp_or_watermark",
    "third_party_content",
)
DECISIONS = {
    "exclude", "internal_only", "anonymize_then_review", "eligible_for_annotation",
}
CHECK_STATUSES = {"absent", "present", "uncertain"}
CHECK_ACTIONS = {"not_applicable", "cleared", "redact", "restrict", "exclude"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path} line {line_number} is not an object")
        rows.append(row)
    return rows


def _render_source(row: Mapping[str, Any], destination: Path, dpi: int) -> tuple[int, int]:
    source = Path(str(row["source_path"]))
    if sha256_file(source) != row["source_file_sha256"]:
        raise ValueError(f"source hash mismatch: {row['record_id']}")
    page_number = int(row["source_page"])
    with pymupdf.open(source) as document:
        if not 1 <= page_number <= len(document):
            raise ValueError(f"source page is outside document: {row['record_id']}")
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72), alpha=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(destination)
        return pixmap.width, pixmap.height


def build_page_review_pack(
    content_manifests: Iterable[Path],
    output_root: Path,
    *,
    phase1_scope: str = "international_candidate",
    dpi: int = 180,
) -> dict[str, Any]:
    """Render a hash-bound, immutable pack for later human source review."""

    if dpi <= 0:
        raise ValueError("dpi must be positive")
    if output_root.exists():
        raise FileExistsError(f"review pack already exists: {output_root}")
    manifest_paths = [Path(path).resolve() for path in content_manifests]
    if not manifest_paths:
        raise ValueError("at least one content manifest is required")
    selected: list[tuple[dict[str, Any], str]] = []
    source_evidence = []
    identifiers: set[str] = set()
    for path in manifest_paths:
        manifest_sha256 = sha256_file(path)
        source_evidence.append({"path": str(path), "sha256": manifest_sha256})
        for row in _read_jsonl(path):
            if row.get("phase1_scope") != phase1_scope:
                continue
            identifier = str(row.get("record_id") or "")
            if (
                not identifier
                or Path(identifier).name != identifier
                or identifier in identifiers
            ):
                raise ValueError(f"unsafe or duplicate content record_id: {identifier!r}")
            identifiers.add(identifier)
            if row.get("benchmark_eligible") is not False:
                raise ValueError(f"source candidate has unexpected benchmark state: {identifier}")
            if row.get("human_content_review") is not False:
                raise ValueError(f"source candidate already claims human review: {identifier}")
            selected.append((row, manifest_sha256))
    if not selected:
        raise ValueError(f"no rows have phase1_scope={phase1_scope!r}")

    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        pack_rows = []
        for row, manifest_sha256 in sorted(
            selected, key=lambda item: str(item[0]["record_id"]),
        ):
            identifier = str(row["record_id"])
            image_path = temporary / "images" / f"{identifier}.png"
            width, height = _render_source(row, image_path, dpi)
            pack_rows.append({
                "review_item_id": identifier,
                "content_record_id": identifier,
                "dataset_id": row["dataset_id"],
                "dataset_doi": row.get("dataset_doi"),
                "source_filename": row["source_filename"],
                "source_path": row["source_path"],
                "source_page": row["source_page"],
                "source_file_sha256": row["source_file_sha256"],
                "source_acquisition_sha256": row["source_acquisition_sha256"],
                "source_inventory_sha256": row.get("source_inventory_sha256"),
                "content_config_sha256": row["content_config_sha256"],
                "content_manifest_sha256": manifest_sha256,
                "provisional_content_class": row["content_class"],
                "provisional_classification_status": row["classification_status"],
                "language": row.get("language"),
                "license_id": row.get("license_id"),
                "render_dpi": dpi,
                "rendered_path": str(output_root / "images" / f"{identifier}.png"),
                "rendered_sha256": sha256_file(image_path),
                "rendered_width_px": width,
                "rendered_height_px": height,
                "review_status": "unreviewed",
                "annotation_eligible": False,
                "benchmark_eligible": False,
            })
        manifest_path = temporary / "review_pack_manifest.jsonl"
        manifest_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in pack_rows),
            encoding="utf-8",
        )
        summary = {
            "review_pack_schema_version": "page_review_pack_v001",
            "scope": "rendered source candidates for human content/privacy review; not Ground Truth",
            "phase1_scope_filter": phase1_scope,
            "render_dpi": dpi,
            "source_content_manifests": source_evidence,
            "review_item_count": len(pack_rows),
            "dataset_counts": {
                dataset_id: sum(row["dataset_id"] == dataset_id for row in pack_rows)
                for dataset_id in sorted({str(row["dataset_id"]) for row in pack_rows})
            },
            "human_review_count": 0,
            "annotation_eligible_count": 0,
            "benchmark_eligible_count": 0,
            "review_pack_manifest_sha256": sha256_file(manifest_path),
        }
        (temporary / "review_pack_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, output_root)
        return {
            **summary,
            "review_pack_summary_sha256": sha256_file(output_root / "review_pack_summary.json"),
        }
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def load_review_items(manifest_path: Path) -> dict[str, dict[str, Any]]:
    items = {}
    for row in _read_jsonl(manifest_path):
        identifier = str(row.get("review_item_id") or "")
        if not identifier or Path(identifier).name != identifier or identifier in items:
            raise ValueError(f"unsafe or duplicate review_item_id: {identifier!r}")
        items[identifier] = row
    if not items:
        raise ValueError("page review pack is empty")
    return items


def _validate_checks(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != set(CHECK_NAMES):
        raise ValueError("all and only required disclosure checks must be supplied")
    for name, check in value.items():
        if not isinstance(check, dict) or set(check) != {"status", "action", "notes"}:
            raise ValueError(f"{name} must contain status, action, and notes")
        status, action = check["status"], check["action"]
        if status not in CHECK_STATUSES or action not in CHECK_ACTIONS:
            raise ValueError(f"{name} has invalid status or action")
        if status == "absent" and action != "not_applicable":
            raise ValueError(f"{name}: absent content requires not_applicable action")
        if status == "present" and action == "not_applicable":
            raise ValueError(f"{name}: present content requires an explicit action")
        if status == "present" and (
            not isinstance(check["notes"], str) or not check["notes"].strip()
        ):
            raise ValueError(f"{name}: present content requires non-empty review notes")
        if status == "uncertain" and action not in {"restrict", "exclude"}:
            raise ValueError(f"{name}: uncertain content must remain restricted or excluded")
        if check["notes"] is not None and not isinstance(check["notes"], str):
            raise ValueError(f"{name}: notes must be a string or null")
    return value


def build_page_review(
    payload: Mapping[str, Any], item: Mapping[str, Any], revision: int,
) -> dict[str, Any]:
    decision = str(payload.get("decision") or "")
    if decision not in DECISIONS:
        raise ValueError("invalid page-review decision")
    reviewer_id = str(payload.get("reviewer_id") or "").strip()
    if not reviewer_id:
        raise ValueError("reviewer_id must be a non-empty human identifier")
    checks = _validate_checks(payload.get("checks"))
    phase1_content = bool(payload.get("phase1_borehole_content"))
    render_complete = bool(payload.get("render_complete"))
    redactions_required = bool(payload.get("redactions_required"))
    if decision == "anonymize_then_review" and not redactions_required:
        raise ValueError("anonymize_then_review requires redactions_required=true")
    if decision == "eligible_for_annotation":
        if not phase1_content:
            raise ValueError("eligible_for_annotation requires phase-1 borehole content")
        if not render_complete:
            raise ValueError("eligible_for_annotation requires a complete readable render")
        if redactions_required:
            raise ValueError("eligible_for_annotation cannot retain required redactions")
        unresolved = [
            name for name, check in checks.items()
            if check["status"] == "uncertain"
            or (check["status"] == "present" and check["action"] != "cleared")
        ]
        if unresolved:
            raise ValueError(
                "eligible_for_annotation has unresolved disclosure checks: " + ", ".join(unresolved)
            )
    notes = payload.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise ValueError("notes must be a string or null")
    return {
        "review_schema_version": "page_content_review_v001",
        "review_item_id": item["review_item_id"],
        "source_file_sha256": item["source_file_sha256"],
        "source_acquisition_sha256": item["source_acquisition_sha256"],
        "content_config_sha256": item["content_config_sha256"],
        "rendered_sha256": item["rendered_sha256"],
        "reviewer_id": reviewer_id,
        "reviewer_provenance": "human_self_attested_not_identity_authenticated",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "phase1_borehole_content": phase1_content,
        "render_complete": render_complete,
        "checks": checks,
        "redactions_required": redactions_required,
        "notes": notes,
        "annotation_eligible": decision == "eligible_for_annotation",
        "benchmark_eligible": False,
        "revision": revision,
    }


def validate_page_review(review: Mapping[str, Any], schema_path: Path) -> None:
    from jsonschema import Draft202012Validator

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(review)
    if review["annotation_eligible"] != (review["decision"] == "eligible_for_annotation"):
        raise ValueError("annotation_eligible is inconsistent with the review decision")
    if review["benchmark_eligible"] is not False:
        raise ValueError("page content review cannot grant benchmark eligibility")
    build_page_review(review, review, int(review["revision"]))


def _validate_review_bindings(
    review: Mapping[str, Any], item: Mapping[str, Any], schema_path: Path,
) -> None:
    validate_page_review(review, schema_path)
    bindings = {
        "review_item_id": item["review_item_id"],
        "source_file_sha256": item["source_file_sha256"],
        "source_acquisition_sha256": item["source_acquisition_sha256"],
        "content_config_sha256": item["content_config_sha256"],
        "rendered_sha256": item["rendered_sha256"],
    }
    for key, expected in bindings.items():
        if review.get(key) != expected:
            raise ValueError(f"review binding mismatch for {item['review_item_id']}: {key}")


def save_page_review(review: Mapping[str, Any], review_root: Path) -> Path:
    review_root.mkdir(parents=True, exist_ok=True)
    path = review_root / f"{review['review_item_id']}.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        history = review_root / "history" / str(review["review_item_id"])
        history.mkdir(parents=True, exist_ok=True)
        archived = history / f"revision_{current['revision']:04d}.json"
        if archived.exists():
            raise FileExistsError(f"history revision already exists: {archived}")
        shutil.copy2(path, archived)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def audit_page_reviews(
    pack_root: Path, review_root: Path, schema_path: Path,
    *,
    eligible_manifest: Path | None = None,
) -> dict[str, Any]:
    """Verify current human reviews and optionally export annotation-eligible items."""

    pack_root = Path(pack_root).resolve()
    review_root = Path(review_root).resolve()
    manifest_path = pack_root / "review_pack_manifest.jsonl"
    summary_path = pack_root / "review_pack_summary.json"
    items = load_review_items(manifest_path)
    pack_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if pack_summary.get("review_pack_manifest_sha256") != sha256_file(manifest_path):
        raise ValueError("review pack manifest differs from pack summary")
    decisions: dict[str, int] = {decision: 0 for decision in sorted(DECISIONS)}
    reviewed = []
    eligible = []
    for identifier, item in sorted(items.items()):
        image_path = pack_root / "images" / f"{identifier}.png"
        if sha256_file(image_path) != item["rendered_sha256"]:
            raise ValueError(f"review image hash mismatch: {identifier}")
        path = review_root / f"{identifier}.json"
        if not path.is_file():
            continue
        review = json.loads(path.read_text(encoding="utf-8"))
        _validate_review_bindings(review, item, schema_path)
        decisions[review["decision"]] += 1
        reviewed.append({"item": item, "review": review, "review_sha256": sha256_file(path)})
        if review["annotation_eligible"]:
            eligible.append({
                **item,
                "human_content_review": True,
                "human_privacy_review": True,
                "content_review_decision": review["decision"],
                "content_review_revision": review["revision"],
                "content_review_reviewer_id": review["reviewer_id"],
                "content_review_sha256": sha256_file(path),
                "annotation_eligible": True,
                "benchmark_eligible": False,
            })
    unreviewed = len(items) - len(reviewed)
    if eligible_manifest is not None:
        if unreviewed:
            raise ValueError(
                f"cannot export annotation-eligible pages while {unreviewed} items are unreviewed"
            )
        eligible_manifest.parent.mkdir(parents=True, exist_ok=True)
        if eligible_manifest.exists():
            raise FileExistsError(f"eligible manifest already exists: {eligible_manifest}")
        eligible_manifest.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in eligible),
            encoding="utf-8",
        )
    return {
        "page_review_audit_schema_version": "page_review_audit_v001",
        "scope": "human source-review status; not geological annotation or Ground Truth",
        "pack_root": str(pack_root),
        "pack_summary_sha256": sha256_file(summary_path),
        "pack_manifest_sha256": sha256_file(manifest_path),
        "review_item_count": len(items),
        "reviewed_item_count": len(reviewed),
        "unreviewed_item_count": unreviewed,
        "decision_counts": decisions,
        "annotation_eligible_count": len(eligible),
        "benchmark_eligible_count": 0,
        "human_ground_truth_count": 0,
        "review_complete": unreviewed == 0,
        "eligible_manifest_path": str(eligible_manifest) if eligible_manifest else None,
        "eligible_manifest_sha256": (
            sha256_file(eligible_manifest) if eligible_manifest is not None else None
        ),
    }


def write_page_review_status(
    pack_root: Path, review_root: Path, schema_path: Path, output_path: Path,
) -> dict[str, Any]:
    """Atomically refresh the non-GT review progress snapshot."""

    result = audit_page_reviews(pack_root, review_root, schema_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output_path)
    return result


def create_page_review_app(
    pack_root: Path, review_root: Path, static_root: Path, schema_path: Path,
    *,
    fixed_reviewer_id: str | None = None,
    status_output: Path | None = None,
):
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse
    except ImportError as exc:
        raise RuntimeError("page review UI requires geologparser[annotation]") from exc

    pack_root = Path(pack_root).resolve()
    review_root = Path(review_root).resolve()
    static_root = Path(static_root).resolve()
    schema_path = Path(schema_path).resolve()
    fixed_reviewer_id = (
        str(fixed_reviewer_id).strip() if fixed_reviewer_id is not None else None
    )
    if fixed_reviewer_id == "":
        raise ValueError("fixed_reviewer_id must be non-empty when configured")
    status_output = Path(status_output).resolve() if status_output is not None else None
    items = load_review_items(pack_root / "review_pack_manifest.jsonl")
    app = FastAPI(title="GeoLogParser Page Content Review", version="v001")
    update_lock = threading.Lock()

    def get_item(identifier: str) -> dict[str, Any]:
        if Path(identifier).name != identifier or identifier not in items:
            raise HTTPException(404, "review item not found")
        return items[identifier]

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (static_root / "index.html").read_text(encoding="utf-8")

    @app.get("/app.js")
    def javascript():
        return FileResponse(static_root / "app.js", media_type="application/javascript")

    @app.get("/style.css")
    def stylesheet():
        return FileResponse(static_root / "style.css", media_type="text/css")

    @app.get("/api/items")
    def list_items():
        result = []
        for identifier, item in sorted(items.items()):
            path = review_root / f"{identifier}.json"
            review = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            if review is not None:
                try:
                    _validate_review_bindings(review, item, schema_path)
                except Exception as exc:
                    raise HTTPException(409, f"stored review failed verification: {exc}") from exc
            result.append({**item, "review": review})
        return result

    @app.get("/api/status")
    def status():
        result = audit_page_reviews(pack_root, review_root, schema_path)
        return {
            **result,
            "fixed_reviewer_id": fixed_reviewer_id,
            "client_reviewer_editable": fixed_reviewer_id is None,
            "status_output_path": str(status_output) if status_output is not None else None,
        }

    @app.get("/api/items/{identifier}/image")
    def image(identifier: str):
        item = get_item(identifier)
        path = (pack_root / "images" / f"{identifier}.png").resolve()
        if pack_root not in path.parents or not path.is_file():
            raise HTTPException(404, "review image not found")
        if sha256_file(path) != item["rendered_sha256"]:
            raise HTTPException(409, "review image hash mismatch")
        return FileResponse(path, media_type="image/png")

    @app.put("/api/items/{identifier}/review")
    def update_review(identifier: str, payload: dict[str, Any]):
        item = get_item(identifier)
        with update_lock:
            path = review_root / f"{identifier}.json"
            current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            if current is not None:
                try:
                    _validate_review_bindings(current, item, schema_path)
                except Exception as exc:
                    raise HTTPException(409, f"stored review failed verification: {exc}") from exc
            expected_revision = current["revision"] if current else 0
            if payload.get("base_revision", 0) != expected_revision:
                raise HTTPException(409, "revision conflict; reload before saving")
            if fixed_reviewer_id is not None:
                supplied = str(payload.get("reviewer_id") or "").strip()
                if supplied and supplied != fixed_reviewer_id:
                    raise HTTPException(403, "reviewer_id differs from the server-fixed reviewer")
                payload = {**payload, "reviewer_id": fixed_reviewer_id}
            try:
                review = build_page_review(payload, item, expected_revision + 1)
                validate_page_review(review, schema_path)
                save_page_review(review, review_root)
                progress = (
                    write_page_review_status(
                        pack_root, review_root, schema_path, status_output,
                    )
                    if status_output is not None
                    else audit_page_reviews(pack_root, review_root, schema_path)
                )
            except Exception as exc:
                raise HTTPException(422, str(exc)) from exc
        return {"review": review, "progress": progress}

    return app
