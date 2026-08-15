#!/usr/bin/env python3
"""Prospective v004 statistics for the frozen California candidate-risk policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, dict]:
    return {row["record_id"]: row for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())}


def aggregate(items: list[tuple[int, int, int]]) -> dict:
    matched, predicted, reference = map(sum, zip(*items))
    precision = matched / predicted if predicted else 0.0
    recall = matched / reference if reference else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"matched": matched, "predicted": predicted, "reference": reference, "precision": precision, "recall": recall, "f1": f1}


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def paired_bootstrap(left: list[tuple[int, int, int]], right: list[tuple[int, int, int]], repetitions: int, rng: random.Random) -> dict:
    if len(left) != len(right):
        raise ValueError("paired inputs differ")
    observed_left, observed_right = aggregate(left), aggregate(right)
    distributions = {name: [] for name in ("precision", "recall", "f1")}
    for _ in range(repetitions):
        indices = [rng.randrange(len(left)) for _ in left]
        l = aggregate([left[index] for index in indices])
        r = aggregate([right[index] for index in indices])
        for name in distributions:
            distributions[name].append(l[name] - r[name])
    return {
        "left": observed_left,
        "right": observed_right,
        "delta_left_minus_right": {
            name: {
                "observed": observed_left[name] - observed_right[name],
                "bootstrap_percentile_95_ci": [percentile(values, 0.025), percentile(values, 0.975)],
                "bootstrap_probability_delta_gt_zero": sum(value > 0 for value in values) / repetitions,
            }
            for name, values in distributions.items()
        },
        "bootstrap_repetitions": repetitions,
        "bootstrap_unit": "document",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--constraint-run", type=Path, default=ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CONSTRAINT_PROSPECTIVE_FORMAL_001")
    ap.add_argument("--risk-run", type=Path, default=ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CANDIDATE_RISK_PROSPECTIVE_FORMAL_001")
    ap.add_argument("--output", type=Path, default=ROOT / "experiments/paper2/analysis/california_candidate_risk_v004.json")
    ap.add_argument("--repetitions", type=int, default=20_000)
    ap.add_argument("--seed", type=int, default=20260815)
    args = ap.parse_args()
    constraint = load(args.constraint_run / "predictions.jsonl")
    risk = load(args.risk_run / "predictions.jsonl")
    ids = sorted(constraint)
    if set(risk) != set(ids):
        raise ValueError("run IDs do not align")
    raw, unselective, selected = [], [], []
    for record_id in ids:
        c, r = constraint[record_id], risk[record_id]
        reference_count = len(c["reference_intervals"])
        raw.append((int(c["raw_match_count"]), len(c["raw_predictions"]), reference_count))
        unselective.append((int(c["constrained_match_count"]), len(c["constrained_predictions"]), reference_count))
        selected.append((int(r["risk_selected_match_count"]), len(r["risk_selected_predictions"]), reference_count))
    metrics = json.loads((args.risk_run / "metrics.json").read_text(encoding="utf-8"))
    errors = int(metrics["accepted_incorrect_additions"])
    actions = int(metrics["accepted_correction_actions"])
    if errors == 0 and actions:
        exact_two_sided_95_upper = 1 - 0.025 ** (1 / actions)
    else:
        exact_two_sided_95_upper = None
    rng = random.Random(args.seed)
    output = {
        "analysis_version": "california_candidate_risk_v004",
        "prospective": True,
        "policy_frozen_before_dataset_acquisition": True,
        "document_count": len(ids),
        "bootstrap_repetitions": args.repetitions,
        "seed": args.seed,
        "risk_vs_raw": paired_bootstrap(selected, raw, args.repetitions, rng),
        "unselective_vs_raw": paired_bootstrap(unselective, raw, args.repetitions, rng),
        "risk_vs_unselective": paired_bootstrap(selected, unselective, args.repetitions, rng),
        "correction_safety": {
            "accepted_actions": actions,
            "observed_incorrect_actions": errors,
            "observed_false_correction_rate": metrics["false_correction_rate"]["value"],
            "exact_two_sided_95_upper_for_zero_errors": exact_two_sided_95_upper,
            "interpretation": "Zero observed errors does not establish a zero population error rate; the exact upper bound quantifies remaining uncertainty.",
        },
        "document_outcomes": metrics["document_outcomes"],
        "accepted_correction_document_count": metrics["accepted_correction_document_count"],
        "changed_document_count": metrics["changed_document_count"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
