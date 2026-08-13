"""Conservative automated licence/source screening for dataset registry entries.

This module deliberately does not claim human privacy review.  It only converts
captured registry evidence into an auditable disposition; uncertain or
uninspected visual content remains quarantined/internal-only.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


OPEN_LICENSE_MARKERS = (
    "cc0", "cc-by", "cc by", "cc-by-sa", "cc by-sa", "creative commons",
    "open government licence",
    "ogl-uk", "public domain", "apache-2.0", "mit license",
)
BLOCKED_STATUS_MARKERS = (
    "blocked", "unclear", "unverified", "needs_manual", "embargo", "conflict",
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _license_is_explicit(value: Any) -> bool:
    text = str(value or "").lower()
    return bool(text) and any(marker in text for marker in OPEN_LICENSE_MARKERS)


def _scan_text_files(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not root.is_dir():
        return findings
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".jsonl", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for category, pattern in (("email_address", EMAIL_RE), ("telephone_like_number", PHONE_RE)):
            count = len(pattern.findall(text))
            if count:
                findings.append({"file": str(path), "category": category, "count": count})
    return findings


def review_registry_entry(entry: Mapping[str, Any], *, dataset_root: Path | None = None) -> dict[str, Any]:
    """Return an evidence-bound automated disposition for one registry entry."""

    identifier = str(entry.get("id") or "")
    license_text = str(entry.get("license") or entry.get("license_id") or "")
    status_text = " ".join(str(entry.get(key) or "") for key in ("status", "access_status", "verification_notes")).lower()
    source_verified = bool(entry.get("url")) and bool(entry.get("source_organization")) and (
        bool(entry.get("downloadable")) or "verified" in status_text or "acquired" in status_text
    )
    license_explicit = _license_is_explicit(license_text) or bool(entry.get("license_url")) and _license_is_explicit(entry.get("allowed_usage"))
    blocked_reasons = [marker for marker in BLOCKED_STATUS_MARKERS if marker in status_text]
    findings = _scan_text_files(dataset_root) if dataset_root else []
    privacy_clear = not findings
    visual_privacy_unknown = str(entry.get("format") or "").lower() not in {"", "tbd"} and any(
        token in str(entry.get("format") or "").lower() for token in ("pdf", "png", "jpg", "image", "dwg")
    )
    reasons: list[str] = []
    if not source_verified:
        reasons.append("source_verification_incomplete")
    if not license_explicit:
        reasons.append("licence_not_explicitly_open")
    if blocked_reasons:
        reasons.append("registry_evidence_contains_blocked_or_pending_marker")
    if findings:
        reasons.append("text_metadata_contains_contact_signal")
    if visual_privacy_unknown:
        reasons.append("visual_content_privacy_not_machine_verifiable")
    if source_verified and license_explicit and not blocked_reasons and not findings:
        decision = "ELIGIBLE"
    elif source_verified and license_explicit and not blocked_reasons and findings:
        decision = "EXCLUDE"
    elif not source_verified or not license_explicit:
        decision = "AMBIGUOUS"
    else:
        decision = "EXCLUDE" if findings else "AMBIGUOUS"
    return {
        "dataset_id": identifier,
        "review_type": "automated_compliance_review",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "source_verified": source_verified,
        "license_explicit": license_explicit,
        "personal_information_risk": "detected" if findings else "not_detected_in_scanned_text",
        "sensitive_location_risk": "unknown_visual_content" if visual_privacy_unknown else "not_detected_in_scanned_text",
        "automated_privacy_scope": "text_metadata_only; visual privacy and sensitive-location absence are not established",
        "evidence": {
            "source_url": entry.get("url"),
            "publisher": entry.get("source_organization"),
            "license": license_text,
            "license_url": entry.get("license_url"),
            "access_status": entry.get("access_status"),
            "local_dataset_root": str(dataset_root) if dataset_root else None,
            "local_evidence_sha256": _sha256(dataset_root / "metadata/acquisition.json") if dataset_root and (dataset_root / "metadata/acquisition.json").is_file() else None,
            "contact_findings": findings,
        },
        "reasons": reasons,
        "human_reviewed": False,
    }


def review_registry(registry: Mapping[str, Any], *, dataset_roots: Mapping[str, Path] | None = None) -> dict[str, Any]:
    roots = dataset_roots or {}
    entries = registry.get("datasets", [])
    if not isinstance(entries, list):
        raise ValueError("registry datasets must be a list")
    reviews = [review_registry_entry(entry, dataset_root=roots.get(str(entry.get("id")))) for entry in entries]
    return {
        "schema_version": "automated_compliance_review_v001",
        "review_type": "automated_compliance_review",
        "human_reviewed": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision_counts": {decision: sum(item["decision"] == decision for item in reviews) for decision in ("ELIGIBLE", "ELIGIBLE_INTERNAL_ONLY", "EXCLUDE", "AMBIGUOUS")},
        "reviews": reviews,
    }
