#!/usr/bin/env python3
"""Quantify California cross-freeze replication with document-cluster bootstrap."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def counts(row: dict, prediction_key: str, match_key: str) -> tuple[int, int, int]:
    return int(row[match_key]), len(row[prediction_key]), len(row["reference_intervals"])


def metrics(items: Iterable[tuple[int, int, int]]) -> dict[str, float | int]:
    values = list(items)
    matched = sum(item[0] for item in values)
    predicted = sum(item[1] for item in values)
    reference = sum(item[2] for item in values)
    precision = matched / predicted if predicted else 0.0
    recall = matched / reference if reference else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "matched": matched,
        "predicted": predicted,
        "reference": reference,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_delta(
    left: list[tuple[int, int, int]],
    right: list[tuple[int, int, int]],
    repetitions: int,
    rng: random.Random,
) -> dict:
    if len(left) != len(right):
        raise ValueError("paired bootstrap inputs differ in length")
    observed_left = metrics(left)
    observed_right = metrics(right)
    distributions = {"precision": [], "recall": [], "f1": []}
    n = len(left)
    for _ in range(repetitions):
        indices = [rng.randrange(n) for _ in range(n)]
        sampled_left = metrics(left[index] for index in indices)
        sampled_right = metrics(right[index] for index in indices)
        for key in distributions:
            distributions[key].append(float(sampled_left[key]) - float(sampled_right[key]))
    deltas = {}
    for key, values in distributions.items():
        deltas[key] = {
            "observed": float(observed_left[key]) - float(observed_right[key]),
            "bootstrap_percentile_95_ci": [percentile(values, 0.025), percentile(values, 0.975)],
            "bootstrap_probability_delta_gt_zero": sum(value > 0 for value in values) / repetitions,
        }
    return {
        "left": observed_left,
        "right": observed_right,
        "delta_left_minus_right": deltas,
        "bootstrap_repetitions": repetitions,
        "bootstrap_unit": "document",
    }


def stratum(reference_count: int) -> str:
    if reference_count <= 12:
        return "5_to_12_intervals"
    if reference_count <= 24:
        return "13_to_24_intervals"
    return "25_to_60_intervals"


def stratified_metrics(rows: dict[str, dict], prediction_key: str, match_key: str) -> dict:
    groups: dict[str, list[tuple[int, int, int]]] = {}
    for row in rows.values():
        item = counts(row, prediction_key, match_key)
        groups.setdefault(stratum(item[2]), []).append(item)
    return {
        name: {"document_count": len(items), **metrics(items)}
        for name, items in sorted(groups.items())
    }


def freeze_analysis(
    rapid: dict[str, dict],
    tesseract: dict[str, dict],
    constrained: dict[str, dict],
    repetitions: int,
    rng: random.Random,
    selective: dict[str, dict] | None = None,
) -> dict:
    ids = sorted(rapid)
    if set(tesseract) != set(ids) or set(constrained) != set(ids):
        raise ValueError("freeze result documents do not align")
    rapid_items = [counts(rapid[item], "predicted_intervals", "matched_interval_count") for item in ids]
    tess_items = [counts(tesseract[item], "predicted_intervals", "matched_interval_count") for item in ids]
    raw_items = [counts(constrained[item], "raw_predictions", "raw_match_count") for item in ids]
    constrained_items = [
        counts(constrained[item], "constrained_predictions", "constrained_match_count") for item in ids
    ]
    output = {
        "document_count": len(ids),
        "ocr_paired_bootstrap": bootstrap_delta(rapid_items, tess_items, repetitions, rng),
        "constraint_paired_bootstrap": bootstrap_delta(constrained_items, raw_items, repetitions, rng),
        "rapidocr_by_reference_interval_count": stratified_metrics(
            rapid, "predicted_intervals", "matched_interval_count"
        ),
        "tesseract_by_reference_interval_count": stratified_metrics(
            tesseract, "predicted_intervals", "matched_interval_count"
        ),
        "raw_by_reference_interval_count": stratified_metrics(
            constrained, "raw_predictions", "raw_match_count"
        ),
        "constrained_by_reference_interval_count": stratified_metrics(
            constrained, "constrained_predictions", "constrained_match_count"
        ),
    }
    if selective is not None:
        if set(selective) != set(ids):
            raise ValueError("selective result documents do not align")
        selective_items = [
            counts(selective[item], "selective_predictions", "selective_match_count")
            for item in ids
        ]
        output["selective_vs_raw_paired_bootstrap"] = bootstrap_delta(
            selective_items, raw_items, repetitions, rng
        )
        output["selective_vs_unselective_paired_bootstrap"] = bootstrap_delta(
            selective_items, constrained_items, repetitions, rng
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/paper1/analysis/california_replication_statistics_v001.json",
    )
    args = parser.parse_args()
    definitions = {
        "v001": {
            "rapid": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_RAPIDOCR_TEST_FORMAL_001/predictions.jsonl",
            "tesseract": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_TESSERACT_TEST_FORMAL_001/predictions.jsonl",
            "constraint": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_CONSTRAINT_TEST_FORMAL_001/predictions.jsonl",
        },
        "v002_external": {
            "rapid": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V002_RAPIDOCR_EXTERNAL_FORMAL_002/predictions.jsonl",
            "tesseract": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V002_TESSERACT_EXTERNAL_FORMAL_002/predictions.jsonl",
            "constraint": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_V002_CONSTRAINT_EXTERNAL_FORMAL_002/predictions.jsonl",
        },
        "v003_prospective": {
            "rapid": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V003_RAPIDOCR_PROSPECTIVE_FORMAL_001/predictions.jsonl",
            "tesseract": ROOT / "results/2026-08-14/P1_CALIFORNIA_WCR_V003_TESSERACT_PROSPECTIVE_FORMAL_001/predictions.jsonl",
            "constraint": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_V003_CONSTRAINT_PROSPECTIVE_FORMAL_001/predictions.jsonl",
            "selective": ROOT / "results/2026-08-14/P2_CALIFORNIA_WCR_V003_SELECTIVE_PROSPECTIVE_FORMAL_001/predictions.jsonl",
        },
    }
    rng = random.Random(args.seed)
    loaded = {
        name: {key: load_jsonl(path) for key, path in paths.items()}
        for name, paths in definitions.items()
    }
    freezes = {
        name: freeze_analysis(
            values["rapid"], values["tesseract"], values["constraint"], args.repetitions, rng,
            values.get("selective"),
        )
        for name, values in loaded.items()
    }

    combined_rapid: list[tuple[int, int, int]] = []
    combined_tess: list[tuple[int, int, int]] = []
    combined_raw: list[tuple[int, int, int]] = []
    combined_constrained: list[tuple[int, int, int]] = []
    for values in loaded.values():
        for record_id in sorted(values["rapid"]):
            combined_rapid.append(counts(values["rapid"][record_id], "predicted_intervals", "matched_interval_count"))
            combined_tess.append(counts(values["tesseract"][record_id], "predicted_intervals", "matched_interval_count"))
            combined_raw.append(counts(values["constraint"][record_id], "raw_predictions", "raw_match_count"))
            combined_constrained.append(
                counts(values["constraint"][record_id], "constrained_predictions", "constrained_match_count")
            )
    payload = {
        "analysis_version": "california_replication_statistics_v001",
        "seed": args.seed,
        "bootstrap_repetitions": args.repetitions,
        "method": "paired nonparametric document-cluster bootstrap with percentile 95% intervals",
        "freezes": freezes,
        "combined_descriptive": {
            "document_count": len(combined_rapid),
            "ocr_paired_bootstrap": bootstrap_delta(
                combined_rapid, combined_tess, args.repetitions, rng
            ),
            "constraint_paired_bootstrap": bootstrap_delta(
                combined_constrained, combined_raw, args.repetitions, rng
            ),
            "interpretation_boundary": "Combined analysis is descriptive because v002 is an external successor selected by the same eligibility policy, not a new population sample with known sampling probabilities.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
