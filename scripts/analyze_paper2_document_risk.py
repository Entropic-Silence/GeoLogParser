#!/usr/bin/env python3
"""Document-cluster risk and net-utility analysis for California v004/v005.

The analysis reuses frozen predictions.  It does not rerun OCR, change the
candidate pool, or tune the addition-only policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]


RUNS = {
    "v004": {
        "unselective": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CONSTRAINT_PROSPECTIVE_FORMAL_001",
        "risk": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CANDIDATE_RISK_PROSPECTIVE_FORMAL_001",
    },
    "v005": {
        "unselective": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CONSTRAINT_EXTERNAL_FORMAL_001",
        "risk": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CANDIDATE_RISK_EXTERNAL_FORMAL_001",
    },
}


def load_rows(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (
            json.loads(line)
            for line in (path / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def pooled(rows: list[dict], variant: str) -> dict:
    matched = sum(row[f"{variant}_match_count"] for row in rows)
    predicted = sum(len(row[f"{variant}_predictions"]) for row in rows)
    reference = sum(len(row["reference_intervals"]) for row in rows)
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


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def paired_bootstrap(rows: list[dict], left: str, right: str, repetitions: int, rng: random.Random) -> dict:
    observed_left = pooled(rows, left)
    observed_right = pooled(rows, right)
    distributions = {"precision": [], "recall": [], "f1": []}
    for _ in range(repetitions):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        left_metrics = pooled(sample, left)
        right_metrics = pooled(sample, right)
        for key in distributions:
            distributions[key].append(left_metrics[key] - right_metrics[key])
    return {
        "left": observed_left,
        "right": observed_right,
        "delta_left_minus_right": {
            key: {
                "observed": observed_left[key] - observed_right[key],
                "document_cluster_percentile_95_ci": [
                    percentile(values, 0.025), percentile(values, 0.975)
                ],
            }
            for key, values in distributions.items()
        },
        "bootstrap_unit": "document",
        "bootstrap_repetitions": repetitions,
    }


def one_sided_zero_event_upper(n: int, alpha: float = 0.05) -> float | None:
    return 1 - alpha ** (1 / n) if n else None


def document_f1(match_count: int, prediction_count: int, reference_count: int) -> float:
    denominator = prediction_count + reference_count
    return 2 * match_count / denominator if denominator else 0.0


def analyze_freeze(name: str, paths: dict[str, Path], repetitions: int, rng: random.Random) -> tuple[dict, list[dict]]:
    unselective = load_rows(paths["unselective"])
    risk = load_rows(paths["risk"])
    if set(unselective) != set(risk):
        raise ValueError(f"{name}: prediction documents differ")
    rows = []
    for record_id in sorted(unselective):
        unselected = unselective[record_id]
        selected = risk[record_id]
        if unselected["raw_predictions"] != selected["raw_predictions"]:
            raise ValueError(f"{name}/{record_id}: raw predictions differ")
        if unselected["reference_intervals"] != selected["reference_intervals"]:
            raise ValueError(f"{name}/{record_id}: references differ")
        raw_match = int(unselected["raw_match_count"])
        sequence_match = int(unselected["constrained_match_count"])
        risk_match = int(selected["risk_selected_match_count"])
        raw_pred = unselected["raw_predictions"]
        sequence_pred = unselected["constrained_predictions"]
        risk_pred = selected["risk_selected_predictions"]
        accepted_actions = len(selected["accepted_additions"])
        row = {
            "freeze": name,
            "record_id": record_id,
            "county": selected.get("county"),
            "reference_intervals": unselected["reference_intervals"],
            "raw_predictions": raw_pred,
            "raw_match_count": raw_match,
            "sequence_predictions": sequence_pred,
            "sequence_match_count": sequence_match,
            "risk_predictions": risk_pred,
            "risk_match_count": risk_match,
            "sequence_correct_interval_gain": sequence_match - raw_match,
            "sequence_erroneous_prediction_gain": (len(sequence_pred) - sequence_match) - (len(raw_pred) - raw_match),
            "risk_correct_interval_gain": risk_match - raw_match,
            "risk_erroneous_prediction_gain": (len(risk_pred) - risk_match) - (len(raw_pred) - raw_match),
            "sequence_worsened": (
                (2 * sequence_match / (len(sequence_pred) + len(unselected["reference_intervals"])))
                < (2 * raw_match / (len(raw_pred) + len(unselected["reference_intervals"]))) - 1e-12
            ),
            "sequence_document_exposed_to_harmful_action": (
                unselected["correction_taxonomy"]["raw_correct_removed"]
                + unselected["correction_taxonomy"]["constrained_incorrect_added"]
            ) > 0,
            "risk_worsened": (
                document_f1(risk_match, len(risk_pred), len(unselected["reference_intervals"]))
                < document_f1(raw_match, len(raw_pred), len(unselected["reference_intervals"])) - 1e-12
            ),
            "accepted_action_count": accepted_actions,
            "risk_accepted_document": accepted_actions > 0,
            "candidate_sequence_changed": sequence_pred != raw_pred,
        }
        rows.append(row)
    accepted_action_counts = [row["accepted_action_count"] for row in rows if row["risk_accepted_document"]]
    changed = sum(row["candidate_sequence_changed"] for row in rows)
    accepted_documents = sum(row["risk_accepted_document"] for row in rows)
    summary = {
        "document_count": len(rows),
        "raw": pooled(rows, "raw"),
        "unselective_sequence": pooled(rows, "sequence"),
        "addition_only_risk": pooled(rows, "risk"),
        "paired_document_bootstrap": {
            "unselective_vs_raw": paired_bootstrap(rows, "sequence", "raw", repetitions, rng),
            "risk_vs_raw": paired_bootstrap(rows, "risk", "raw", repetitions, rng),
            "risk_vs_unselective": paired_bootstrap(rows, "risk", "sequence", repetitions, rng),
        },
        "net_utility": {
            "unselective_correct_interval_gain": sum(row["sequence_correct_interval_gain"] for row in rows),
            "unselective_erroneous_prediction_gain": sum(row["sequence_erroneous_prediction_gain"] for row in rows),
            "unselective_worsened_document_count": sum(row["sequence_worsened"] for row in rows),
            "unselective_documents_exposed_to_harmful_action": sum(
                row["sequence_document_exposed_to_harmful_action"] for row in rows
            ),
            "risk_correct_interval_gain": sum(row["risk_correct_interval_gain"] for row in rows),
            "risk_erroneous_prediction_gain": sum(row["risk_erroneous_prediction_gain"] for row in rows),
            "risk_worsened_document_count": sum(row["risk_worsened"] for row in rows),
            "correct_intervals_added_per_100_documents": {
                "unselective": 100 * sum(row["sequence_correct_interval_gain"] for row in rows) / len(rows),
                "risk": 100 * sum(row["risk_correct_interval_gain"] for row in rows) / len(rows),
            },
        },
        "review_and_coverage": {
            "documents_with_changed_candidate_sequence": changed,
            "accepted_document_count": accepted_documents,
            "accepted_document_coverage_all_documents": accepted_documents / len(rows),
            "accepted_document_coverage_changed_documents": accepted_documents / changed if changed else None,
            "review_or_abstain_document_count": changed - accepted_documents,
            "review_or_abstain_rate_all_documents": (changed - accepted_documents) / len(rows),
            "accepted_actions_per_accepted_document": {
                "minimum": min(accepted_action_counts) if accepted_action_counts else None,
                "median": percentile(accepted_action_counts, 0.5) if accepted_action_counts else None,
                "maximum": max(accepted_action_counts) if accepted_action_counts else None,
                "mean": sum(accepted_action_counts) / len(accepted_action_counts) if accepted_action_counts else None,
                "values": accepted_action_counts,
            },
        },
    }
    return summary, rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/paper2/analysis/california_document_risk_v001.json",
    )
    arguments = parser.parse_args()
    rng = random.Random(arguments.seed)
    summaries = {}
    all_rows = []
    for name, paths in RUNS.items():
        summary, rows = analyze_freeze(name, paths, arguments.repetitions, rng)
        summaries[name] = summary
        all_rows.extend(rows)
    accepted_documents = [row for row in all_rows if row["risk_accepted_document"]]
    accepted_actions = sum(row["accepted_action_count"] for row in accepted_documents)
    accepted_counties = sorted({row["county"] for row in accepted_documents if row.get("county")})
    payload = {
        "analysis_version": "california_document_risk_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD",
        "policy_status": "frozen before v004 and unchanged for v005",
        "candidate_pool_statement": "Each freeze compares raw, unselective, and addition-only outputs derived from the identical frozen positioned-text run.",
        "bootstrap_unit": "document",
        "bootstrap_repetitions": arguments.repetitions,
        "seed": arguments.seed,
        "freezes": summaries,
        "combined_confirmatory": {
            "document_count": len(all_rows),
            "accepted_document_count": len(accepted_documents),
            "accepted_action_count": accepted_actions,
            "observed_worsened_document_count": sum(row["risk_worsened"] for row in accepted_documents),
            "observed_incorrect_action_count": sum(max(0, row["risk_erroneous_prediction_gain"]) for row in accepted_documents),
            "document_level_one_sided_95_upper_bound": one_sided_zero_event_upper(len(accepted_documents)),
            "action_level_one_sided_95_upper_bound_iid_assumption": one_sided_zero_event_upper(accepted_actions),
            "accepted_county_count": len(accepted_counties),
            "accepted_counties_anonymized": [f"county_group_{index:02d}" for index, _ in enumerate(accepted_counties, start=1)],
            "county_group_one_sided_95_upper_bound_sensitivity": one_sided_zero_event_upper(len(accepted_counties)),
            "source_program_count": 1,
            "template_group_count": None,
            "correct_intervals_added_per_100_documents": 100 * sum(row["risk_correct_interval_gain"] for row in all_rows) / len(all_rows),
            "review_or_abstain_document_count": sum(
                row["candidate_sequence_changed"] and not row["risk_accepted_document"] for row in all_rows
            ),
            "interpretation": "Documents, not actions, are the primary safety unit. The action bound is secondary because actions cluster within accepted documents. County groups are a sensitivity unit, not independent source families; all accepted documents remain within one California WCR program and a reliable template grouping is unavailable.",
        },
        "document_rows": all_rows,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(arguments.output)


if __name__ == "__main__":
    main()
