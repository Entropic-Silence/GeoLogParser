"""Two-extractor plus adjudicator protocol for non-Gold Silver labels.

Extractors are injected callables.  The orchestrator never passes prediction A
to extractor B (or vice versa); only the adjudicator receives both outputs and
the source item.  Outputs are immutable and labelled SILVER, never GOLD.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Mapping, Sequence
from dataclasses import asdict

from geologparser.constraints import default_engine
from geologparser.schema import validate_record


Extractor = Callable[[Mapping[str, Any]], Mapping[str, Any]]
Adjudicator = Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], Sequence[Any]], Mapping[str, Any]]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _record_from_prediction(value: Mapping[str, Any]) -> Mapping[str, Any]:
    record = value.get("record") if isinstance(value, Mapping) and "record" in value else value
    validate_record(record)
    return record


def _default_adjudicator(source: Mapping[str, Any], prediction_a: Mapping[str, Any], prediction_b: Mapping[str, Any], constraints: Sequence[Any]) -> dict[str, Any]:
    record_a = _record_from_prediction(prediction_a)
    record_b = _record_from_prediction(prediction_b)
    agreement = _canonical(record_a) == _canonical(record_b)
    return {
        "record": record_a if agreement else None,
        "agreement_status": "AGREEMENT" if agreement else "DISAGREEMENT",
        "confidence": 1.0 if agreement else 0.0,
        "adjudication_reason": "byte_identical_predictions" if agreement else "extractor_predictions_differ; source_reinspection_required",
    }


def run_silver_case(
    source_item: Mapping[str, Any], extractor_a: Extractor, extractor_b: Extractor,
    *, adjudicator: Adjudicator | None = None, confidence_threshold: float = 0.95,
) -> dict[str, Any]:
    """Run A and B independently, then let C adjudicate their outputs."""

    if not source_item.get("item_id"):
        raise ValueError("source item requires item_id")
    # Deliberately separate calls and inputs: no prediction object is shared.
    prediction_a = dict(extractor_a(dict(source_item)))
    prediction_b = dict(extractor_b(dict(source_item)))
    record_a = _record_from_prediction(prediction_a)
    record_b = _record_from_prediction(prediction_b)
    engine = default_engine()
    constraint_a = [asdict(result) for result in engine.evaluate(record_a)]
    constraint_b = [asdict(result) for result in engine.evaluate(record_b)]
    resolve = adjudicator or _default_adjudicator
    decision = dict(resolve(dict(source_item), dict(prediction_a), dict(prediction_b), (constraint_a, constraint_b)))
    status = str(decision.get("agreement_status") or "DISAGREEMENT")
    confidence = float(decision.get("confidence", 0.0))
    if status == "AGREEMENT" and confidence >= confidence_threshold and decision.get("record") is not None:
        validate_record(decision["record"])
        tier = "SILVER_HIGH_CONFIDENCE"
    elif status == "AGREEMENT":
        tier = "SILVER_UNCERTAIN"
    else:
        tier = "SILVER_UNCERTAIN"
    hard_case = status != "AGREEMENT" or any(result.get("violations") for result in constraint_a + constraint_b)
    return {
        "item_id": str(source_item["item_id"]),
        "ground_truth_tier": tier,
        "prediction_a": {"record": record_a, "sha256": _digest(record_a), "extractor_id": prediction_a.get("extractor_id", "A")},
        "prediction_b": {"record": record_b, "sha256": _digest(record_b), "extractor_id": prediction_b.get("extractor_id", "B")},
        "constraint_results": {"A": constraint_a, "B": constraint_b},
        "silver_label": decision.get("record"),
        "agreement_status": status,
        "confidence": confidence,
        "adjudication_reason": decision.get("adjudication_reason"),
        "hard_case": hard_case,
        "human_ground_truth": False,
        "accuracy_metrics": None,
    }


def build_silver_dataset(
    source_items: Sequence[Mapping[str, Any]], output_root: Path,
    extractor_a: Extractor, extractor_b: Extractor, *, adjudicator: Adjudicator | None = None,
    confidence_threshold: float = 0.95,
) -> dict[str, Any]:
    output_root = Path(output_root).resolve()
    if output_root.exists():
        raise FileExistsError(f"silver output already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    rows = []
    try:
        for source in source_items:
            rows.append(run_silver_case(source, extractor_a, extractor_b, adjudicator=adjudicator, confidence_threshold=confidence_threshold))
        predictions = temporary / "silver_labels.jsonl"
        predictions.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        hard_cases = temporary / "hard_cases.jsonl"
        hard_cases.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows if row["hard_case"]), encoding="utf-8")
        summary = {
            "dataset_version": "silver_machine_adjudicated_v001", "ground_truth_tier": "SILVER",
            "source_item_count": len(rows), "high_confidence_count": sum(row["ground_truth_tier"] == "SILVER_HIGH_CONFIDENCE" for row in rows),
            "uncertain_count": sum(row["ground_truth_tier"] == "SILVER_UNCERTAIN" for row in rows),
            "hard_case_count": sum(row["hard_case"] for row in rows), "human_ground_truth_count": 0,
            "accuracy_metrics": None, "scope": "machine-adjudicated labels for diagnostics/training candidates; not Gold",
            "extractor_a_id": "injected", "extractor_b_id": "injected", "confidence_threshold": confidence_threshold,
        }
        (temporary / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output_root.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary, output_root)
        return summary
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
