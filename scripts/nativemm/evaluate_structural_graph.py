#!/usr/bin/env python3
"""Evaluate Qwen NativeMM structural graphs on BGS v001 development labels.

The graph itself is scored for JSON/schema validity and structural evidence;
boundary depths are produced only by the deterministic geometry decoder.  The
script never opens a frozen external manifest unless explicitly passed one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft7Validator

from geologparser.nativemm import decode_structural_graph


def _load_gold(path: Path) -> dict[tuple[str, int], dict]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        parts = row["sample_id"].split("::page-")
        if len(parts) != 2:
            continue
        result[(parts[0], int(parts[1].split("::", 1)[0]))] = row
    return result


def _match(pred: list[float], ref: list[float], tolerance: float) -> dict:
    used: set[int] = set()
    tp = 0
    for value in pred:
        candidates = [(abs(value - target), index) for index, target in enumerate(ref) if index not in used and abs(value - target) <= tolerance]
        if candidates:
            _, index = min(candidates)
            used.add(index)
            tp += 1
    fp, fn = len(pred) - tp, len(ref) - tp
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 1.0,
    }


def evaluate(prediction_path: Path, gold_path: Path, schema_path: Path) -> dict:
    gold = _load_gold(gold_path)
    validator = Draft7Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    rows = []
    total = {"tp": 0, "fp": 0, "fn": 0}
    for line in prediction_path.read_text(encoding="utf-8").splitlines():
        prediction = json.loads(line)
        key = (prediction["record_id"], int(prediction["page"]))
        graph = prediction.get("graph")
        schema_errors = list(validator.iter_errors(graph)) if graph is not None else []
        decoded = decode_structural_graph(graph)
        reference = gold.get(key)
        if reference is None:
            raise KeyError(f"No explicit gold row for {key} in {gold_path}")
        reference_depths = [float(item["depth_m"]) for item in reference["boundaries"]]
        metrics = _match(list(decoded.geometry.boundaries_m), reference_depths, 0.05)
        for name in total:
            total[name] += metrics[name]
        rows.append({
            "record_id": key[0],
            "page": key[1],
            "json_valid": graph is not None,
            "schema_valid": graph is not None and not schema_errors,
            "schema_errors": [error.message for error in schema_errors[:5]],
            "selected_events": decoded.selected_events,
            "rejected_events": decoded.rejected_events,
            "decoded_boundaries_m": list(decoded.geometry.boundaries_m),
            "reference_boundaries_m": reference_depths,
            "boundary_depth_at_0_05m": metrics,
            "warnings": list(decoded.warnings),
        })
    micro = _match([], [], 0.05)
    micro.update(total)
    micro.update({
        "precision": total["tp"] / (total["tp"] + total["fp"]) if total["tp"] + total["fp"] else 0.0,
        "recall": total["tp"] / (total["tp"] + total["fn"]) if total["tp"] + total["fn"] else 0.0,
        "f1": 2 * total["tp"] / (2 * total["tp"] + total["fp"] + total["fn"]) if 2 * total["tp"] + total["fp"] + total["fn"] else 1.0,
    })
    return {
        "experiment_id": "P2_QWEN38_FP8_STRUCTURAL_GRAPH_EVAL_001",
        "prediction_path": str(prediction_path),
        "gold_path": str(gold_path),
        "schema_path": str(schema_path),
        "rows": rows,
        "json_valid_rate": sum(int(row["json_valid"]) for row in rows) / len(rows) if rows else 0.0,
        "schema_valid_rate": sum(int(row["schema_valid"]) for row in rows) / len(rows) if rows else 0.0,
        "micro_boundary_depth_at_0_05m": micro,
        "bgs_v003_accessed": False,
        "scope": "BGS v001 development only; frozen external sets excluded",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=Path("/data/GeoLogParser/datasets/paper2_nativemm_dense_boundary_v001/development.jsonl"))
    parser.add_argument("--schema", type=Path, default=Path("schemas/native_mm_structural_graph_v001.schema.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.predictions, args.gold, args.schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
