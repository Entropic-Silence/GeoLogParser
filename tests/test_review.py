import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from geologparser.review import TimingEventStore, build_review_queue


ROOT = Path(__file__).resolve().parents[1]


def sample_record():
    return json.loads((ROOT / "examples/boreholes/synthetic_valid.json").read_text(encoding="utf-8"))


def test_review_queue_combines_missing_low_confidence_and_constraint_reasons():
    record = sample_record()
    record["borehole"]["final_depth_m"]["value"] = None
    record["borehole"]["borehole_id"]["confidence"] = 0.2
    record["intervals"][0]["bottom_depth_m"]["value"] = -1
    items = build_review_queue("a1", record, low_confidence_threshold=0.7)
    by_path = {item.field_path: item for item in items}
    assert "MISSING_REQUIRED_MVP_FIELD" in by_path["borehole.final_depth_m"].reason_codes
    assert "LOW_CONFIDENCE" in by_path["borehole.borehole_id"].reason_codes
    assert "DEPTH_NOT_INCREASING" in by_path["intervals[0].bottom_depth_m"].reason_codes


def test_timing_store_writes_append_only_real_duration(tmp_path: Path, monkeypatch):
    store = TimingEventStore(tmp_path / "timing.jsonl")
    times = iter([
        datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 12, 10, 2, tzinfo=timezone.utc),
    ])
    monkeypatch.setattr(store, "_now", lambda: next(times))
    started = store.start("a1", "reviewer")
    completed = store.complete(started["session_id"], 4)
    assert completed["duration_seconds"] == 120
    assert completed["fields_corrected_per_minute"] == 2
    assert len((tmp_path / "timing.jsonl").read_text().splitlines()) == 2


def test_timing_store_rejects_invalid_completion(tmp_path: Path):
    store = TimingEventStore(tmp_path / "timing.jsonl")
    with pytest.raises(ValueError):
        store.complete("missing", 1)
