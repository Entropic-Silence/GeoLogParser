import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_codex_internal_visual_pilot_is_explicitly_scoped_and_traceable():
    record = json.loads(
        (ROOT / "experiments/paper2/analysis/codex_internal_visual_baseline_v001.json").read_text(
            encoding="utf-8"
        )
    )
    assert record["model"]["model_id"] == "gpt-5.6-sol"
    assert record["model"]["reasoning_effort"] == "xhigh"
    assert record["model"]["reproducible_outside_host"] is False
    assert record["aggregate"]["documents"] == 5
    assert record["aggregate"]["reference_intervals"] == 91
    assert record["aggregate"]["matched_intervals"] == 91
    assert record["aggregate"]["f1"] == 1.0
    assert "not a full California-cohort benchmark" in record["interpretation"]


def test_codex_internal_visual_prompt_hash_and_prediction_count_are_frozen():
    prompt = ROOT / "prompts/codex_visual_interval_source_units_v001.md"
    record = json.loads(
        (ROOT / "experiments/paper2/analysis/codex_internal_visual_baseline_v001.json").read_text(
            encoding="utf-8"
        )
    )
    assert hashlib.sha256(prompt.read_bytes()).hexdigest() == record["prompt"]["sha256"]
    rows = [
        json.loads(line)
        for line in (ROOT / "experiments/paper2/analysis/codex_internal_visual_predictions_v001.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(rows) == 5
    assert sum(len(row["intervals"]) for row in rows) == 91
