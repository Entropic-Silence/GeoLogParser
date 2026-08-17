#!/usr/bin/env python3
"""Ablate California sequence scoring on the frozen positioned-text pool.

No OCR is rerun.  Every ablation consumes the same semantically eligible
hypotheses reconstructed from the archived OCR-region files.  The full variant
must reproduce the archived constrained predictions exactly.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random

import fitz

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from run_california_constraint_sequence import (
    GEOLOGY_TERMS,
    as_predictions,
    hypotheses,
    load_regions,
    transition_score,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZES = {
    "v004": {
        "manifest": ROOT / "datasets/manifests/california_wcr_gold_v004.jsonl",
        "raw": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V004_RAPIDOCR_PROSPECTIVE_FORMAL_001",
        "constraint": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CONSTRAINT_PROSPECTIVE_FORMAL_001",
    },
    "v005": {
        "manifest": ROOT / "datasets/manifests/california_wcr_gold_v005.jsonl",
        "raw": ROOT / "results/2026-08-15/P1_CALIFORNIA_WCR_V005_RAPIDOCR_EXTERNAL_FORMAL_001",
        "constraint": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CONSTRAINT_EXTERNAL_FORMAL_001",
    },
}


def load_jsonl(path: Path) -> dict[str, dict]:
    return {
        row["record_id"]: row
        for row in (
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def page_dimensions(pdf_path: Path, page_number: int, dpi: int = 300) -> tuple[int, int]:
    with fitz.open(pdf_path) as document:
        rectangle = document[page_number - 1].rect
        return round(rectangle.width * dpi / 72), round(rectangle.height * dpi / 72)


def monotonic_edge(left: dict, right: dict) -> float | None:
    if (right["page"], right["y"]) <= (left["page"], left["y"]):
        return None
    if right["top"] < left["top"] or left["bottom"] - right["top"] > 1.0:
        return None
    return 0.0


def continuity_edge(left: dict, right: dict) -> float | None:
    base = monotonic_edge(left, right)
    if base is None:
        return None
    gap = abs(left["bottom"] - right["top"])
    if gap <= 0.05:
        return 5.0
    if gap <= 1.0:
        return 2.0 - gap
    return -min(6.0, math.log1p(gap))


def select(candidates: list[dict], edge_name: str, semantic_bonus: bool = True) -> list[dict]:
    ordered = sorted(candidates, key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]))
    if not ordered:
        return []
    edge_function = {
        "monotonic": monotonic_edge,
        "continuity": continuity_edge,
        "full": transition_score,
    }[edge_name]
    node_scores = []
    for item in ordered:
        score = item["node_score"]
        if not semantic_bonus and GEOLOGY_TERMS.search(item["description"]):
            score -= 1.0
        node_scores.append(score)
    scores = [score - 0.0005 * item["top"] for score, item in zip(node_scores, ordered)]
    parents: list[int | None] = [None] * len(ordered)
    lengths = [1] * len(ordered)
    for right_index, right in enumerate(ordered):
        for left_index in range(max(0, right_index - 400), right_index):
            edge = edge_function(ordered[left_index], right)
            if edge is None:
                continue
            candidate_score = scores[left_index] + node_scores[right_index] + edge
            candidate_length = lengths[left_index] + 1
            if candidate_score > scores[right_index] or (
                abs(candidate_score - scores[right_index]) < 1e-9
                and candidate_length > lengths[right_index]
            ):
                scores[right_index] = candidate_score
                parents[right_index] = left_index
                lengths[right_index] = candidate_length
    end = max(range(len(ordered)), key=lambda index: (scores[index], lengths[index]))
    path = []
    while end is not None:
        path.append(ordered[end])
        end = parents[end]
    return list(reversed(path))


def boundaries(rows: list[dict]) -> set[tuple[float, float]]:
    return {
        (round(float(row["top_depth_m"]), 5), round(float(row["bottom_depth_m"]), 5))
        for row in rows
    }


def pooled(rows: list[dict], variant: str) -> dict:
    references = [row["reference_intervals"] for row in rows]
    predictions = [row["variants"][variant] for row in rows]
    metrics = boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05)
    return {key: value.to_dict() for key, value in metrics.items()}


def correction_safety(rows: list[dict], variant: str) -> dict:
    totals = {
        "raw_correct_removed": 0,
        "raw_incorrect_removed": 0,
        "variant_correct_added": 0,
        "variant_incorrect_added": 0,
    }
    harmful_documents = 0
    f1_worsened_documents = 0
    for row in rows:
        reference = boundaries(row["reference_intervals"])
        raw = boundaries(row["variants"]["raw_parser"])
        changed = boundaries(row["variants"][variant])
        document = {
            "raw_correct_removed": len((raw & reference) - changed),
            "raw_incorrect_removed": len((raw - reference) - changed),
            "variant_correct_added": len((changed & reference) - raw),
            "variant_incorrect_added": len((changed - reference) - raw),
        }
        for key, value in document.items():
            totals[key] += value
        harmful_documents += (
            document["raw_correct_removed"] + document["variant_incorrect_added"] > 0
        )
        raw_f1 = 2 * len(raw & reference) / (len(raw) + len(reference)) if raw or reference else 0.0
        variant_f1 = 2 * len(changed & reference) / (len(changed) + len(reference)) if changed or reference else 0.0
        f1_worsened_documents += variant_f1 < raw_f1 - 1e-12
    actions = sum(totals.values())
    harmful = totals["raw_correct_removed"] + totals["variant_incorrect_added"]
    return {
        "correction_taxonomy": totals,
        "automatic_actions": actions,
        "harmful_actions": harmful,
        "false_correction_rate": harmful / actions if actions else None,
        "documents_with_any_harmful_action": harmful_documents,
        "documents_with_lower_interval_f1_than_raw": f1_worsened_documents,
    }


def f1_from_rows(rows: list[dict], variant: str) -> float:
    matched = sum(row["document_metrics"][variant]["matched"] for row in rows)
    predicted = sum(len(row["variants"][variant]) for row in rows)
    reference = sum(len(row["reference_intervals"]) for row in rows)
    precision = matched / predicted if predicted else 0.0
    recall = matched / reference if reference else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def bootstrap(rows: list[dict], variants: list[str], repetitions: int, rng: random.Random) -> dict:
    distributions = {variant: [] for variant in variants}
    for _ in range(repetitions):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        for variant in variants:
            distributions[variant].append(f1_from_rows(sample, variant))
    output = {}
    for variant, values in distributions.items():
        ordered = sorted(values)
        output[variant] = {
            "f1": f1_from_rows(rows, variant),
            "document_cluster_percentile_95_ci": [
                ordered[int(0.025 * (len(ordered) - 1))],
                ordered[int(0.975 * (len(ordered) - 1))],
            ],
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments/paper2/analysis/california_candidate_pool_ablation_v001.json",
    )
    arguments = parser.parse_args()
    rng = random.Random(arguments.seed)
    all_rows = []
    freeze_summaries = {}
    variants = [
        "raw_parser",
        "candidate_pool_without_sequence",
        "monotonic_sequence",
        "continuity_sequence",
        "column_stable_without_semantic_bonus",
        "complete_sequence",
    ]
    for freeze, paths in FREEZES.items():
        manifest = load_jsonl(paths["manifest"])
        raw = load_jsonl(paths["raw"] / "predictions.jsonl")
        constrained = load_jsonl(paths["constraint"] / "predictions.jsonl")
        if set(manifest) != set(raw) or set(raw) != set(constrained):
            raise ValueError(f"{freeze}: records do not align")
        freeze_rows = []
        for record_id in sorted(raw):
            candidate_pool = []
            source = manifest[record_id]
            for evidence in raw[record_id]["evidence"]:
                page = int(evidence["page"])
                width, height = page_dimensions(Path(source["pdf_path"]), page)
                regions = load_regions(paths["raw"] / evidence["ocr_regions_path"])
                candidate_pool.extend(hypotheses(regions, width, height, page))
            variant_predictions = {
                "raw_parser": raw[record_id]["predicted_intervals"],
                "candidate_pool_without_sequence": as_predictions(sorted(
                    candidate_pool,
                    key=lambda item: (item["page"], item["y"], item["top"], item["bottom"]),
                )),
                "monotonic_sequence": as_predictions(select(candidate_pool, "monotonic")),
                "continuity_sequence": as_predictions(select(candidate_pool, "continuity")),
                "column_stable_without_semantic_bonus": as_predictions(
                    select(candidate_pool, "full", semantic_bonus=False)
                ),
                "complete_sequence": as_predictions(select(candidate_pool, "full")),
            }
            archived = constrained[record_id]["constrained_predictions"]
            if boundaries(variant_predictions["complete_sequence"]) != boundaries(archived):
                raise ValueError(f"{freeze}/{record_id}: full ablation does not reproduce archived sequence")
            matches = {}
            for variant, predictions in variant_predictions.items():
                matched, missing, extra = match_intervals_by_boundaries(
                    constrained[record_id]["reference_intervals"], predictions, tolerance_m=0.05
                )
                matches[variant] = {
                    "matched": len(matched), "missing": len(missing), "extra": len(extra)
                }
            row = {
                "freeze": freeze,
                "record_id": record_id,
                "reference_intervals": constrained[record_id]["reference_intervals"],
                "candidate_count": len(candidate_pool),
                "variants": variant_predictions,
                "document_metrics": matches,
            }
            freeze_rows.append(row)
            all_rows.append(row)
        freeze_summaries[freeze] = {
            "document_count": len(freeze_rows),
            "candidate_count": sum(row["candidate_count"] for row in freeze_rows),
            "metrics": {variant: pooled(freeze_rows, variant) for variant in variants},
            "correction_safety": {
                variant: correction_safety(freeze_rows, variant)
                for variant in variants if variant != "raw_parser"
            },
            "document_cluster_f1": bootstrap(
                freeze_rows, variants, arguments.repetitions, rng
            ),
        }
    payload = {
        "analysis_version": "california_candidate_pool_ablation_v001",
        "evidence_tier": "PUBLISHED_MANUAL_TRANSCRIPTION_GOLD",
        "source": "archived RapidOCR positioned regions from California v004/v005",
        "candidate_pool_control": "All sequence variants within a document consume the same semantically eligible hypothesis pool; OCR and matching are fixed.",
        "reproduction_gate": "complete_sequence boundary sets exactly reproduce every archived constrained prediction",
        "limitations": [
            "Semantic eligibility is part of candidate construction and cannot be removed while keeping the candidate pool identical.",
            "The semantic ablation removes only the geology-term node-score bonus.",
            "The California candidate pool contains one RapidOCR reader, so multi-reader agreement is not independently ablatable.",
            "These variants identify contributions of sequence scoring components, not causal effects of all geological constraints in the full project.",
        ],
        "variants": {
            "raw_parser": "archived first-pass parser output",
            "candidate_pool_without_sequence": "all semantically eligible positioned hypotheses, ordered and deduplicated",
            "monotonic_sequence": "node scores plus document order and nondecreasing depth",
            "continuity_sequence": "monotonic sequence plus adjacent-boundary continuity score",
            "column_stable_without_semantic_bonus": "continuity plus column-stability penalty, excluding the geology-term node bonus",
            "complete_sequence": "column-stable sequence plus geology-term node bonus",
        },
        "bootstrap_unit": "document",
        "bootstrap_repetitions": arguments.repetitions,
        "seed": arguments.seed,
        "freezes": freeze_summaries,
        "combined_descriptive": {
            "document_count": len(all_rows),
            "candidate_count": sum(row["candidate_count"] for row in all_rows),
            "metrics": {variant: pooled(all_rows, variant) for variant in variants},
            "correction_safety": {
                variant: correction_safety(all_rows, variant)
                for variant in variants if variant != "raw_parser"
            },
            "document_cluster_f1": bootstrap(all_rows, variants, arguments.repetitions, rng),
            "interpretation": "Descriptive pooling of two record-disjoint deterministic cohorts; no population sampling weights are available.",
        },
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(arguments.output)


if __name__ == "__main__":
    main()
