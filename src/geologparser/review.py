"""Deterministic review-queue generation and append-only timing events."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from geologparser.constraints import default_engine


@dataclass(frozen=True)
class ReviewItem:
    annotation_id: str
    field_path: str
    priority: str
    reason_codes: tuple[str, ...]
    confidence: float | None
    source_page: int | None
    source_bbox: list[float] | None


MVP_BOREHOLE_FIELDS = (
    "borehole_id", "collar_elevation_m", "final_depth_m", "groundwater_depth_m",
)
MVP_INTERVAL_FIELDS = (
    "top_depth_m", "bottom_depth_m", "thickness_m", "lithology_raw", "description_raw",
)


def build_review_queue(
    annotation_id: str,
    record: Mapping[str, Any],
    low_confidence_threshold: float = 0.7,
) -> list[ReviewItem]:
    reasons: dict[str, set[str]] = {}
    envelopes: dict[str, Mapping[str, Any]] = {}

    def inspect(path: str, envelope: Mapping[str, Any], required: bool) -> None:
        envelopes[path] = envelope
        value = envelope.get("value")
        if required and (value is None or value == ""):
            reasons.setdefault(path, set()).add("MISSING_REQUIRED_MVP_FIELD")
        confidence = envelope.get("confidence")
        if confidence is not None and float(confidence) < low_confidence_threshold:
            reasons.setdefault(path, set()).add("LOW_CONFIDENCE")
        if envelope.get("validation_status") in {"warning", "failed", "needs_review"}:
            reasons.setdefault(path, set()).add("FIELD_VALIDATION_STATUS")

    for name, envelope in record.get("borehole", {}).items():
        if isinstance(envelope, Mapping):
            inspect(f"borehole.{name}", envelope, name in MVP_BOREHOLE_FIELDS)
    for index, interval in enumerate(record.get("intervals", ())):
        for name, envelope in interval.items():
            if name == "interval_id" or not isinstance(envelope, Mapping):
                continue
            inspect(f"intervals[{index}].{name}", envelope, name in MVP_INTERVAL_FIELDS)

    for result in default_engine().evaluate(record):
        for violation in result.violations:
            for path in violation.affected_fields:
                reasons.setdefault(path, set()).add(violation.code)

    items = []
    for path, codes in sorted(reasons.items()):
        envelope = envelopes.get(path, {})
        priority = "high" if any(
            code in {"MISSING_REQUIRED_MVP_FIELD", "DEPTH_NOT_INCREASING", "DEPTH_SEQUENCE_INVERSION", "FINAL_DEPTH_MISMATCH"}
            for code in codes
        ) else "medium"
        items.append(ReviewItem(
            annotation_id=annotation_id,
            field_path=path,
            priority=priority,
            reason_codes=tuple(sorted(codes)),
            confidence=envelope.get("confidence"),
            source_page=envelope.get("source_page"),
            source_bbox=envelope.get("display_bbox") or envelope.get("source_bbox"),
        ))
    return items


class TimingEventStore:
    """Local append-only session events; active sessions are process-local."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._active: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _append(self, event: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(dict(event), ensure_ascii=False, sort_keys=True) + "\n")

    def start(self, annotation_id: str, annotator_id: str) -> dict[str, Any]:
        now = self._now()
        event = {
            "event": "review_started", "session_id": str(uuid.uuid4()),
            "annotation_id": annotation_id, "annotator_id": annotator_id,
            "timestamp": now.isoformat(),
        }
        with self._lock:
            self._active[event["session_id"]] = event | {"started_at": now}
            self._append(event)
        return event

    def complete(self, session_id: str, corrected_fields: int) -> dict[str, Any]:
        if corrected_fields < 0:
            raise ValueError("corrected_fields must be non-negative")
        with self._lock:
            started = self._active.pop(session_id, None)
            if started is None:
                raise ValueError("unknown or already completed review session")
            now = self._now()
            duration = (now - started["started_at"]).total_seconds()
            event = {
                "event": "review_completed", "session_id": session_id,
                "annotation_id": started["annotation_id"],
                "annotator_id": started["annotator_id"],
                "timestamp": now.isoformat(), "duration_seconds": duration,
                "corrected_fields": corrected_fields,
                "fields_corrected_per_minute": (
                    corrected_fields / (duration / 60) if duration > 0 else None
                ),
            }
            self._append(event)
        return event


def review_items_to_dict(items: Sequence[ReviewItem]) -> list[dict[str, Any]]:
    return [asdict(item) for item in items]
