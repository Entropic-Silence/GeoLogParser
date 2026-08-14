#!/usr/bin/env python3
"""Run a secondary, post-result component ablation on frozen v2 artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from geologparser.evaluation import boundary_matched_interval_metrics, match_intervals_by_boundaries
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
NUMBER = r"\d+(?:[.,]\d+)?"
LEGACY_RANGE = re.compile(rf"^\s*({NUMBER})\s*(?:m\s*)?[-–—]\s*({NUMBER})\s*m?\b", re.I)
LEGACY_BOUNDARY = re.compile(rf"^\s*({NUMBER})\s*m?(?:\s+|$)", re.I)


def legacy_normalize(text: str) -> str:
    text = re.sub(r"^\s*[|}\]\[]+\s*(?=\d)", "", text)
    text = re.sub(r"(?<=\d)[lI](?=\s*m?\s*[-–—])", "1", text)
    text = re.sub(r"(?<=[-–—])[lI](?=\s*m?\b)", "1", text)
    return re.sub(r"^\s*[lI](?=\s*[-–—])", "1", text)


def legacy_sections(text: str) -> list[list[tuple[float, float]]]:
    lines = text.splitlines()
    starts = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        if (
            re.search(r"\bbis\s+tiefe\b", lowered)
            or re.search(r"\bbis\s+tief(?:e|em)?\b", lowered)
            or re.match(r"^\s*bis\s+m\b", lowered)
            or (re.search(r"\b(?:tiefe\s*m|tiefem)\b", lowered) and re.search(r"beschreibung.*bohrgut", lowered))
            or re.search(r"beschreibung.*bohrgut", lowered)
        ):
            starts.append(index)
    sections = []
    for start in starts:
        ranges, boundaries = [], []
        started, blank_count = False, 0
        for raw_line in lines[start + 1:start + 56]:
            line = legacy_normalize(raw_line)
            if started and re.search(r"grundwasser|bohrkote|verrohrung|bohrmeissel|bohrwerkzeug|hydrologie", line, re.I):
                break
            if not line.strip():
                blank_count += int(started)
                if started and blank_count >= 4:
                    break
                continue
            match = LEGACY_RANGE.match(line)
            if match:
                top, bottom = (float(value.replace(",", ".")) for value in match.groups())
                if 0 <= top < bottom:
                    ranges.append((top, bottom))
                    started, blank_count = True, 0
                continue
            match = LEGACY_BOUNDARY.match(line)
            if match:
                boundary = float(match.group(1).replace(",", "."))
                remainder = line[match.end():]
                if 0 < boundary and (not remainder.strip() or re.search(r"[A-Za-zÄÖÜäöüß]", remainder)):
                    boundaries.append(boundary)
                    started, blank_count = True, 0
        if ranges:
            candidate = sorted(set(ranges))
        elif boundaries:
            ordered = []
            for boundary in boundaries:
                if not ordered or boundary != ordered[-1]:
                    ordered.append(boundary)
            increasing = []
            for boundary in ordered:
                if not increasing or boundary > increasing[-1]:
                    increasing.append(boundary)
            values = [0.0, *increasing]
            candidate = [
                (values[index], values[index + 1])
                for index in range(len(values) - 1)
                if values[index] < values[index + 1]
            ]
        else:
            continue
        if candidate and candidate not in sections:
            sections.append(candidate)
    return sections


def legacy_choose(text: str) -> tuple[tuple[float, float], ...]:
    sections = legacy_sections(text)
    return tuple(max(sections, key=len, default=[]))


def as_pairs(intervals: list[dict]) -> tuple[tuple[float, float], ...]:
    return tuple((float(row["top_depth_m"]), float(row["bottom_depth_m"])) for row in intervals)


def as_intervals(pairs) -> list[dict]:
    return [
        {"top_depth_m": top, "bottom_depth_m": bottom, "thickness_m": bottom - top}
        for top, bottom in pairs
    ]


def exact(reference: list[dict], prediction: list[dict]) -> bool:
    matches, missing, extra = match_intervals_by_boundaries(reference, prediction, 0.05)
    return len(matches) == len(reference) == len(prediction) and not missing and not extra


def v1_acceptance(first, triggers: list[str], candidate_support: list[dict]):
    v1_triggers = [trigger for trigger in triggers if trigger != "incomplete_top_boundary"]
    if not v1_triggers:
        return first
    counts = Counter({as_pairs(row["intervals"]): int(row["support"]) for row in candidate_support})
    eligible = {
        section: support
        for section, support in counts.items()
        if support >= 2 and (not first or set(first).issubset(set(section)))
    }
    ranked = sorted(eligible.items(), key=lambda item: (item[1], len(item[0]), item[0]), reverse=True)
    if not ranked:
        return first
    top, support = ranked[0]
    next_support = ranked[1][1] if len(ranked) > 1 else -1
    return top if support > next_support and top != first else first


def metric_dicts(references, predictions) -> dict:
    return {
        name: value.to_dict()
        for name, value in boundary_matched_interval_metrics(references, predictions, tolerance_m=0.05).items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    source_metrics = json.loads((args.source_run / "metrics.json").read_text(encoding="utf-8"))
    source_run = json.loads((args.source_run / "run.json").read_text(encoding="utf-8"))
    if source_metrics.get("policy_version") != "v2" or source_metrics.get("evaluation_role") != "heldout":
        raise ValueError("source run must be the frozen v2 held-out experiment")
    rows = [
        json.loads(line)
        for line in (args.source_run / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    variants = {name: [] for name in ("legacy_parser_first_pass", "v2_first_pass", "v2_parser_v1_acceptance", "full_v2")}
    references = []
    output_rows = []
    for row in rows:
        reference = row["reference_intervals"]
        references.append(reference)
        text_path = args.source_run / "case_artifacts" / row["record_id"] / "first_pass_psm3.txt"
        legacy = as_intervals(legacy_choose(text_path.read_text(encoding="utf-8")))
        first_pairs = as_pairs(row["first_pass_intervals"])
        old_accept = as_intervals(v1_acceptance(first_pairs, row["triggers"], row["candidate_support"]))
        values = {
            "legacy_parser_first_pass": legacy,
            "v2_first_pass": row["first_pass_intervals"],
            "v2_parser_v1_acceptance": old_accept,
            "full_v2": row["final_intervals"],
        }
        for name, prediction in values.items():
            variants[name].append(prediction)
        output_rows.append({
            "record_id": row["record_id"],
            "reference_intervals": reference,
            "variants": values,
        })

    full_first = variants["v2_first_pass"]
    metrics = {
        "scope": "secondary heldout component ablation on frozen v2 artifacts",
        "analysis_role": "secondary_descriptive_post_result_ablation",
        "source_experiment_id": source_run["experiment_id"],
        "source_metrics_sha256": file_sha256(args.source_run / "metrics.json"),
        "source_predictions_sha256": file_sha256(args.source_run / "predictions.jsonl"),
        "document_count": len(rows),
        "reference_interval_count": sum(len(row) for row in references),
        "variants": {},
    }
    for name, predictions in variants.items():
        changed = [index for index, prediction in enumerate(predictions) if prediction != full_first[index]]
        successful = sum(
            not exact(references[index], full_first[index]) and exact(references[index], predictions[index])
            for index in changed
        )
        false = sum(
            exact(references[index], full_first[index]) and not exact(references[index], predictions[index])
            for index in changed
        )
        metrics["variants"][name] = {
            "interval_metrics": metric_dicts(references, predictions),
            "document_full_exact_count": sum(exact(reference, prediction) for reference, prediction in zip(references, predictions)),
            "changed_document_count": len(changed),
            "correction_success_rate": {
                "value": successful / len(changed) if changed else None,
                "numerator": successful,
                "denominator": len(changed),
            },
            "false_correction_rate": {
                "value": false / len(changed) if changed else None,
                "numerator": false,
                "denominator": len(changed),
            },
        }

    git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    run = create_run_directory(args.results_root, {
        "experiment_id": args.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": source_run["dataset_version"],
        "split_version": source_run["split_version"],
        "model": "frozen_v2_artifact_secondary_ablation",
        "model_revision": git_commit,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "gpu_used": False},
        "software": {"python": subprocess.run(["python3", "--version"], text=True, capture_output=True).stdout.strip()},
        "config": {
            "source_run": str(args.source_run),
            "analysis_role": "secondary_descriptive_post_result_ablation",
            "no_policy_retuning": True,
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
    })
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8",
    )
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "run.log").write_text(f"documents={len(rows)}\nstatus=completed\n", encoding="utf-8")
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
