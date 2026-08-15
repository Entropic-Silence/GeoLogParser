#!/usr/bin/env python3
"""Post-hoc split-leakage diagnostic on the frozen California v001 outputs.

The parser and OCR predictions are frozen before this analysis.  Random
record-level test sets are sampled from the combined development+test freeze and
compared with the county-first grouped test partition.  This is a leakage
diagnostic, not a new model-training benchmark.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from geologparser.evaluation import boundary_matched_interval_metrics

ROOT = Path(__file__).resolve().parents[1]
SPLIT = ROOT / "datasets/splits/california_wcr_gold_split_v001.json"
DEV = ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_DEV_003/predictions.jsonl"
TEST = ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001/predictions.jsonl"
OUTPUT = ROOT / "experiments/paper1/analysis/california_random_vs_grouped_split_v001.json"


def load(path: Path) -> dict[str, dict]:
    return {row["record_id"]: row for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())}


def score(rows: list[dict]) -> dict:
    references = [[row for row in item["reference_intervals"]] for item in rows]
    predictions = [[row for row in item["predicted_intervals"]] for item in rows]
    metrics = boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05)
    return {
        "document_count": len(rows),
        "reference_interval_count": sum(len(x) for x in references),
        "predicted_interval_count": sum(len(x) for x in predictions),
        "document_exact_count": sum(bool(row.get("document_full_exact")) for row in rows),
        "interval_precision": metrics["interval_precision"].value,
        "interval_recall": metrics["interval_recall"].value,
        "interval_f1": metrics["interval_f1"].value,
    }


def mean_std(values: list[float]) -> dict:
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1) if len(values) > 1 else 0.0
    return {"mean": mean, "std": variance ** 0.5, "min": min(values), "max": max(values)}


def main() -> None:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    combined = load(DEV) | load(TEST)
    if set(combined) != set(split["development"]) | set(split["test"]):
        raise ValueError("frozen prediction IDs do not match v001 split")
    grouped_ids = list(split["test"])
    grouped_rows = [combined[key] for key in grouped_ids]
    grouped = score(grouped_rows)
    all_ids = sorted(combined)
    dev_ids = set(split["development"])
    random_scores = []
    overlap = []
    for seed in range(100):
        rng = random.Random(seed)
        ids = rng.sample(all_ids, len(grouped_ids))
        rows = [combined[key] for key in ids]
        random_scores.append(score(rows))
        overlap.append(sum(key in dev_ids for key in ids) / len(ids))
    output = {
        "analysis_scope": "post-hoc random-record versus county-first grouped split leakage diagnostic",
        "prediction_conditioning": "all OCR predictions frozen before split analysis; no retraining or parser selection",
        "combined_document_count": len(all_ids),
        "grouped_test": grouped,
        "random_test": {
            "sample_count": len(random_scores),
            "test_size": len(grouped_ids),
            "metrics": {key: mean_std([row[key] for row in random_scores]) for key in ("interval_precision", "interval_recall", "interval_f1")},
            "development_overlap_fraction": mean_std(overlap),
            "seeds": list(range(100)),
        },
        "interpretation_limits": [
            "Random samples reuse records from the original development partition and therefore quantify leakage risk rather than independent generalization.",
            "The grouped test partition is county-first and the parser was frozen before its evaluation; this is not a controlled retraining comparison.",
        ],
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
