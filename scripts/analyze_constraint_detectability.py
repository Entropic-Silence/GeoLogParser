#!/usr/bin/env python3
"""Measure which real extraction errors are visible to frozen constraints.

Constraint decisions are computed from predictions only.  Reference intervals
are read afterwards solely to label observed omission, spurious-boundary, and
semantic events for post-hoc detectability analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from geologparser.constraints import load_engine_config


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/constraints/default_v001.yaml"
DEFAULT_SOURCES = {
    "bgs_rapidocr": ROOT / "results/2026-08-15/P1_BGS_OFFSHORE_V001_RAPIDOCR_CROSS_SOURCE_FORMAL_001/predictions.jsonl",
    "bgs_tesseract": ROOT / "results/2026-08-15/P1_BGS_OFFSHORE_V001_TESSERACT_CROSS_SOURCE_FORMAL_001/predictions.jsonl",
    "raft_rapidocr": ROOT / "results/2026-08-14/P1_USGS_RAFT_RIVER_RAPIDOCR_INTERVAL_FORMAL_001/predictions.jsonl",
    "raft_tesseract": ROOT / "results/2026-08-14/P1_USGS_RAFT_RIVER_TESSERACT_INTERVAL_FORMAL_001/predictions.jsonl",
    "usgs142_tesseract": ROOT / "results/2026-08-14/P1_USGS142_CROSS_SOURCE_INTERVAL_FORMAL_002/predictions.jsonl",
    "usgs144_tesseract": ROOT / "results/2026-08-14/P1_USGS144_CROSS_SOURCE_INTERVAL_FORMAL_001/predictions.jsonl",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def error_events(row: dict) -> set[str]:
    events: set[str] = set()
    if row.get("unmatched_reference_indices"):
        events.add("boundary_omission")
    if row.get("unmatched_prediction_indices"):
        events.add("spurious_interval")
    matched = int(row.get("matched_interval_count", 0))
    exact = int(row.get("matched_lithology_exact_count", 0))
    if matched > exact:
        events.add("lithology_semantic_error")
    return events


def analyze(name: str, path: Path, engine) -> dict:
    rows = load_rows(path)
    code_counts: Counter[str] = Counter()
    event_docs: Counter[str] = Counter()
    event_docs_flagged: Counter[str] = Counter()
    records = []
    for row in rows:
        predicted = row.get("predicted_intervals", [])
        record = {"borehole": {}, "intervals": predicted}
        results = engine.evaluate(record)
        violations = [v for result in results for v in result.violations]
        codes = sorted({v.code for v in violations})
        events = sorted(error_events(row))
        for code in codes:
            code_counts[code] += 1
        for event in events:
            event_docs[event] += 1
            if codes:
                event_docs_flagged[event] += 1
        records.append({
            "record_id": row.get("record_id"),
            "predicted_interval_count": len(predicted),
            "observed_error_events": events,
            "constraint_violation_codes": codes,
            "constraint_violation_count": len(violations),
        })
    return {
        "source": name,
        "prediction_path": str(path),
        "prediction_sha256": sha256(path),
        "document_count": len(rows),
        "documents_with_any_constraint_violation": sum(bool(r["constraint_violation_codes"]) for r in records),
        "constraint_violation_code_document_counts": dict(sorted(code_counts.items())),
        "observed_error_event_document_counts": dict(sorted(event_docs.items())),
        "observed_error_event_documents_flagged_by_any_constraint": dict(sorted(event_docs_flagged.items())),
        "event_detectability": {
            event: (event_docs_flagged[event] / count if count else None)
            for event, count in sorted(event_docs.items())
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/analysis/cross_source_constraint_detectability_v001.json")
    parser.add_argument("--constraint-config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    engine = load_engine_config(args.constraint_config)
    sources = {name: path for name, path in DEFAULT_SOURCES.items() if path.is_file()}
    if not sources:
        raise SystemExit("no frozen prediction sources found")
    output = {
        "analysis_scope": "post-hoc reference-blind constraint detectability on frozen real cross-source interval predictions",
        "reference_use": "references are read only after constraint evaluation to label observed error events",
        "constraint_config": str(args.constraint_config.relative_to(ROOT)),
        "constraint_config_sha256": sha256(args.constraint_config),
        "sources": [analyze(name, path, engine) for name, path in sorted(sources.items())],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        source["source"]: {
            "documents": source["document_count"],
            "violating_documents": source["documents_with_any_constraint_violation"],
            "events": source["observed_error_event_document_counts"],
            "detectability": source["event_detectability"],
        }
        for source in output["sources"]
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
