"""Revisioned human content-review storage for quarantined CAD derivatives."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any


CHECK_NAMES = (
    "organization_or_project",
    "person_or_signature",
    "contact_or_address",
    "coordinates_or_sensitive_location",
    "stamp_or_watermark",
    "third_party_content",
)


def load_derivatives(manifest_path: Path) -> dict[str, dict]:
    rows = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        identifier = row["source_record_id"]
        if identifier in rows:
            raise ValueError(f"duplicate derivative source_record_id: {identifier}")
        rows[identifier] = row
    return rows


def build_review(payload: dict[str, Any], derivative: dict, revision: int) -> dict:
    decision = str(payload["decision"])
    checks = payload["checks"]
    if set(checks) != set(CHECK_NAMES):
        raise ValueError("all and only the required content checks must be supplied")
    if any(check["status"] not in {"absent", "present", "uncertain"} for check in checks.values()):
        raise ValueError("invalid content-check status")
    conversion_complete = bool(payload["conversion_complete"])
    if derivative["conversion_may_be_incomplete"] and conversion_complete:
        raise ValueError("a derivative with conversion warnings cannot be declared complete")
    if decision == "eligible_for_annotation":
        if not conversion_complete:
            raise ValueError("eligible_for_annotation requires a complete conversion")
        if not bool(payload["single_borehole_log"]):
            raise ValueError("eligible_for_annotation requires a single-borehole log")
        if any(check["status"] != "absent" for check in checks.values()):
            raise ValueError("eligible_for_annotation requires all disclosure checks absent")
        if bool(payload.get("redactions_required", False)):
            raise ValueError("eligible_for_annotation cannot retain unresolved redactions")
    return {
        "review_schema_version": "cad_content_review_v001",
        "source_record_id": derivative["source_record_id"],
        "source_sha256": derivative["source_sha256"],
        "derivative_sha256": derivative["png_sha256"],
        "reviewer_id": str(payload["reviewer_id"]),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "single_borehole_log": bool(payload["single_borehole_log"]),
        "conversion_complete": conversion_complete,
        "checks": checks,
        "redactions_required": bool(payload.get("redactions_required", False)),
        "notes": payload.get("notes"),
        "benchmark_eligible": False,
        "revision": revision,
    }


def validate_review_schema(review: dict, schema_path: Path) -> None:
    from jsonschema import Draft202012Validator

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_record = {key: value for key, value in review.items() if key != "revision"}
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(
        schema_record
    )


def save_review(review: dict, review_root: Path) -> Path:
    review_root.mkdir(parents=True, exist_ok=True)
    path = review_root / f"{review['source_record_id']}.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        history = review_root / "history" / review["source_record_id"]
        history.mkdir(parents=True, exist_ok=True)
        archived = history / f"revision_{current['revision']:04d}.json"
        if archived.exists():
            raise FileExistsError(f"history revision already exists: {archived}")
        shutil.copy2(path, archived)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def create_cad_review_app(
    derivative_manifest: Path, derivative_root: Path, review_root: Path,
    static_root: Path, schema_path: Path,
):
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, HTMLResponse
    except ImportError as exc:
        raise RuntimeError("CAD review UI requires geologparser[annotation]") from exc

    derivatives = load_derivatives(Path(derivative_manifest))
    derivative_root = Path(derivative_root).resolve()
    review_root = Path(review_root).resolve()
    static_root = Path(static_root).resolve()
    schema_path = Path(schema_path).resolve()
    app = FastAPI(title="GeoLogParser CAD Content Review", version="v001")

    def derivative(identifier: str) -> dict:
        if Path(identifier).name != identifier or identifier not in derivatives:
            raise HTTPException(404, "derivative not found")
        return derivatives[identifier]

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
        items = []
        for identifier, row in sorted(derivatives.items()):
            review_path = review_root / f"{identifier}.json"
            review = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else None
            items.append({
                "source_record_id": identifier,
                "pixel_dimensions": row["pixel_dimensions"],
                "conversion_may_be_incomplete": row["conversion_may_be_incomplete"],
                "review": review,
            })
        return items

    @app.get("/api/items/{identifier}/image")
    def image(identifier: str):
        row = derivative(identifier)
        path = (derivative_root / identifier / "model.png").resolve()
        if derivative_root not in path.parents or not path.is_file():
            raise HTTPException(404, "derivative image not found")
        if row["png_sha256"] != __import__("hashlib").sha256(path.read_bytes()).hexdigest():
            raise HTTPException(409, "derivative image hash mismatch")
        return FileResponse(path, media_type="image/png")

    @app.put("/api/items/{identifier}/review")
    def update_review(identifier: str, payload: dict[str, Any]):
        row = derivative(identifier)
        path = review_root / f"{identifier}.json"
        current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        expected_revision = current["revision"] if current else 0
        if payload.get("base_revision", 0) != expected_revision:
            raise HTTPException(409, "revision conflict; reload before saving")
        try:
            review = build_review(payload, row, expected_revision + 1)
            validate_review_schema(review, schema_path)
            save_review(review, review_root)
        except Exception as exc:
            raise HTTPException(422, str(exc)) from exc
        return review

    return app
