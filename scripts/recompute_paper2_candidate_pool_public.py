#!/usr/bin/env python3
"""Recompute Paper II sequence variants from the deidentified public pool."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from geologparser.paper2_sequence import select_sequence


ROOT = Path(__file__).resolve().parents[1]


def monotonic_edge(left: dict, right: dict) -> float | None:
    if (right["page_order"], right["y_norm"]) <= (left["page_order"], left["y_norm"]):
        return None
    if right["top_ft"] < left["top_ft"] or left["bottom_ft"] - right["top_ft"] > 1.0:
        return None
    return 0.0


def continuity_edge(left: dict, right: dict) -> float | None:
    if monotonic_edge(left, right) is None:
        return None
    gap = abs(left["bottom_ft"] - right["top_ft"])
    if gap <= 0.05:
        return 5.0
    if gap <= 1.0:
        return 2.0 - gap
    return -min(6.0, math.log1p(gap))


def full_edge(left: dict, right: dict) -> float | None:
    base = continuity_edge(left, right)
    if base is None:
        return None
    return base - 4.0 * (abs(left["x_top_norm"] - right["x_top_norm"]) + abs(left["x_bottom_norm"] - right["x_bottom_norm"])) - 0.15 * max(0, right["page_order"] - left["page_order"] - 1)


def as_intervals(path: list[dict]) -> list[dict]:
    return [{
        "top_depth_m": item["top_depth_m"],
        "bottom_depth_m": item["bottom_depth_m"],
        "thickness_m": item["bottom_depth_m"] - item["top_depth_m"],
    } for item in path]


def variants(row: dict) -> dict[str, list[dict]]:
    pool = [dict(item, top=item["top_ft"], bottom=item["bottom_ft"], page=item["page_order"], y=item["y_norm"], x_top=item["x_top_norm"], x_bottom=item["x_bottom_norm"], node_score=item["raw_node_score"]) for item in row["candidate_pool"]]
    ordered = sorted(pool, key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]))
    semantic_pool = [dict(item) for item in pool]
    for item in semantic_pool:
        item["node_score"] = item["raw_node_score"] - (1.0 if item["geology_term"] else 0.0)
    complete = select_sequence(pool, full_edge)
    return {
        "candidate_pool_without_sequence": as_intervals(ordered),
        "monotonic_sequence": as_intervals(select_sequence(pool, monotonic_edge)),
        "continuity_sequence": as_intervals(select_sequence(pool, continuity_edge)),
        "column_stable_without_semantic_bonus": as_intervals(select_sequence(semantic_pool, full_edge)),
        "complete_sequence": as_intervals(complete),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "experiments/paper2/public/candidate_pool_v001.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/public/candidate_pool_recomputed_v001.jsonl")
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    output = []
    for row in rows:
        result = {"record_key": row["record_key"], "cohort": row["cohort"], "variants": variants(row), "reference_intervals": row["reference_intervals"], "raw_intervals": row["raw_intervals"]}
        actual = tuple(sorted((round(x["top_depth_m"], 6), round(x["bottom_depth_m"], 6)) for x in result["variants"]["complete_sequence"]))
        archived = tuple(sorted((round(x["top_depth_m"], 6), round(x["bottom_depth_m"], 6)) for x in row["archived_complete_intervals"]))
        if actual != archived:
            raise ValueError(f"{row['record_key']}: public recomputation differs from archived complete path")
        output.append(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
