#!/usr/bin/env python3
"""Nested source-disjoint joint event-owner sequence decoding.

This diagnostic keeps the existing candidate probabilities fixed and changes
only the sequence decoder.  Candidates are grouped into mutually exclusive
visual events; dynamic programming then applies an owner-switch penalty to
avoid alternating between incompatible printed, graphical, and terminal
metadata evidence within a page.  Threshold and penalty are selected on the
non-target source folds only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import time


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fold_id(record_id: str, folds: int) -> int:
    return int(hashlib.sha256(record_id.encode()).hexdigest()[:8], 16) % folds


def refs(row: dict) -> list[float]:
    return sorted({float(interval[key]) for interval in row["intervals"] for key in ("top_depth_m", "bottom_depth_m")})


def boundary_metrics(predictions: dict[str, list[float]], references: dict[str, list[float]], tolerance: float) -> dict:
    tp = fp = fn = 0
    for record_id, expected in references.items():
        remaining = list(expected)
        for prediction in predictions.get(record_id, []):
            if not remaining:
                fp += 1
                continue
            index = min(range(len(remaining)), key=lambda i: abs(prediction - remaining[i]))
            if abs(prediction - remaining[index]) <= tolerance:
                tp += 1
                remaining.pop(index)
            else:
                fp += 1
        fn += len(remaining)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "critical_numerical_error_rate": fp / (tp + fp) if tp + fp else None,
    }


def interval_metrics(predictions: dict[str, list[float]], references: dict[str, list[float]], tolerance: float) -> dict:
    tp = fp = fn = 0
    for record_id, expected_boundaries in references.items():
        predicted = sorted(predictions.get(record_id, []))
        expected = list(zip(expected_boundaries, expected_boundaries[1:]))
        actual = list(zip(predicted, predicted[1:]))
        remaining = list(expected)
        for top, bottom in actual:
            hit = next((i for i, pair in enumerate(remaining)
                        if abs(top - pair[0]) <= tolerance and abs(bottom - pair[1]) <= tolerance), None)
            if hit is None:
                fp += 1
            else:
                tp += 1
                remaining.pop(hit)
        fn += len(remaining)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
    }


def owner(candidate: dict) -> str:
    source = str(candidate.get("candidate_source") or "")
    if source == "graphic_scale_transition":
        return "graphic"
    if source == "metadata_final_depth":
        return "terminal"
    return "printed"


def deduplicate(candidates: list[dict], threshold: float) -> list[dict]:
    selected: dict[tuple[int, int], dict] = {}
    for candidate in candidates:
        probability = float(candidate.get("probability") or 0.0)
        if probability < threshold:
            continue
        page = int(candidate.get("page") or 0)
        value = float(candidate["value_m"])
        key = (page, round(value * 20))
        if key not in selected or probability > float(selected[key].get("probability") or 0.0):
            selected[key] = candidate
    return list(selected.values())


def joint_sequence(candidates: list[dict], threshold: float, switch_penalty: float) -> list[float]:
    rows = deduplicate(candidates, threshold)
    if not rows:
        return []
    body = [row for row in rows if owner(row) != "terminal"]
    terminal = [row for row in rows if owner(row) == "terminal"]
    body.sort(key=lambda row: (int(row.get("page") or 0), float(row.get("bbox", [0, 0, 0, 0])[1]), float(row["value_m"])))
    groups: list[list[dict]] = []
    for row in body:
        center_y = sum(float(v) for v in row.get("bbox", [0, 0, 0, 0])[1:4:2]) / 2.0
        if groups:
            prior = groups[-1][-1]
            prior_y = sum(float(v) for v in prior.get("bbox", [0, 0, 0, 0])[1:4:2]) / 2.0
            same_event = int(prior.get("page") or 0) == int(row.get("page") or 0) and abs(center_y - prior_y) <= 10.0
        else:
            same_event = False
        if same_event:
            groups[-1].append(row)
        else:
            groups.append([row])
    if terminal:
        groups.append(terminal)
    ordered = [candidate for group in groups for candidate in group]
    group_ids = []
    for group_id, group in enumerate(groups):
        group_ids.extend([group_id] * len(group))
    scores = []
    previous: list[tuple[int, str] | None] = []
    threshold_logit = math.log(max(1e-6, threshold) / max(1e-6, 1 - threshold))
    for index, candidate in enumerate(ordered):
        probability = float(candidate.get("probability") or 0.0)
        node = math.log(max(1e-6, probability) / max(1e-6, 1 - probability)) - threshold_logit
        scores.append(node)
        previous.append(None)
        for left in range(index):
            prior = ordered[left]
            if group_ids[left] >= group_ids[index] or float(candidate["value_m"]) <= float(prior["value_m"]) + 0.025:
                continue
            transition = -switch_penalty if owner(candidate) != owner(prior) else 0.0
            edge = 0.12 - 0.015 * max(0.0, float(candidate["value_m"]) - float(prior["value_m"]) - 50.0)
            proposed = scores[left] + node + edge + transition
            if proposed > scores[index]:
                scores[index] = proposed
                previous[index] = (left, owner(prior))
    end = max(range(len(ordered)), key=lambda index: scores[index])
    selected: list[dict] = []
    while end >= 0:
        selected.append(ordered[end])
        link = previous[end]
        end = link[0] if link is not None else -1
    selected.reverse()
    output: list[float] = []
    for candidate in selected:
        value = float(candidate["value_m"])
        if not output or abs(value - output[-1]) > 0.05:
            output.append(value)
    return output


def bundle(predictions: dict[str, list[float]], references: dict[str, list[float]]) -> dict:
    return {
        "boundary": boundary_metrics(predictions, references, 0.05),
        "interval": interval_metrics(predictions, references, 0.05),
        "document_count": len(predictions),
        "reference_boundary_count": sum(len(values) for values in references.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--candidate-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    started = time.perf_counter()
    manifest = load_jsonl(args.manifest)
    report = json.loads(args.candidate_report.read_text(encoding="utf-8"))
    rows = {row["record_id"]: row for row in report["predictions"]}
    references = {row["record_id"]: refs(row) for row in manifest}
    predictions: dict[str, list[float]] = {}
    policies: dict[str, dict] = {}
    route_rows: list[dict] = []
    thresholds = [0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24, 0.28, 0.32]
    penalties = [0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75]
    for fold in range(args.folds):
        train_ids = [row["record_id"] for row in manifest if fold_id(row["record_id"], args.folds) != fold]
        test_ids = [row["record_id"] for row in manifest if fold_id(row["record_id"], args.folds) == fold]
        best = None
        for threshold in thresholds:
            for penalty in penalties:
                candidate_predictions = {
                    record_id: joint_sequence(rows[record_id].get("ranked_candidates", []), threshold, penalty)
                    for record_id in train_ids
                }
                interval = interval_metrics(candidate_predictions, {record_id: references[record_id] for record_id in train_ids}, 0.05)
                boundary = boundary_metrics(candidate_predictions, {record_id: references[record_id] for record_id in train_ids}, 0.05)
                key = (interval["f1"], boundary["f1"], boundary["precision"], -threshold, -penalty)
                if best is None or key > best[0]:
                    best = (key, threshold, penalty)
        assert best is not None
        _, threshold, penalty = best
        policies[str(fold)] = {"threshold": threshold, "owner_switch_penalty": penalty, "train_document_count": len(train_ids)}
        for record_id in test_ids:
            predicted = joint_sequence(rows[record_id].get("ranked_candidates", []), threshold, penalty)
            predictions[record_id] = predicted
            route_rows.append({"record_id": record_id, "fold": fold, "threshold": threshold, "owner_switch_penalty": penalty, "predicted_boundaries_m": predicted})
    result = {
        "experiment_id": args.experiment_id,
        "status": "completed_nested_development",
        "method_version": "bgs_joint_event_owner_sequence_v030",
        "manifest": str(args.manifest),
        "manifest_sha256": sha256(args.manifest),
        "candidate_report": str(args.candidate_report),
        "candidate_report_sha256": sha256(args.candidate_report),
        "document_count": len(manifest),
        "overall": bundle(predictions, references),
        "routing_policy_by_fold": policies,
        "predictions": route_rows,
        "reference_blinding": "candidate probabilities fixed before target references; threshold and owner penalty fitted only on non-target source folds",
        "wall_time_seconds": time.perf_counter() - started,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["overall"], indent=2))


if __name__ == "__main__":
    main()
