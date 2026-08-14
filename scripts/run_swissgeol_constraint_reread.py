#!/usr/bin/env python3
"""Evaluate a frozen raster-only constraint-guided reread policy.

The policy was developed on the v001 Swissgeol source-agreement subset.  It is
eligible for the held-out method tier only when the evaluation manifest has no
record overlap with that development manifest.  Reference values are loaded
only after all extraction and reread decisions have been frozen in memory.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
import platform
import re
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from geologparser.datasets.swissgeol import choose_interval_section
from geologparser.evaluation import (
    boundary_matched_interval_metrics,
    match_intervals_by_boundaries,
)
from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEVELOPMENT = Path(
    "/data/GeoLogParser/datasets/public/swissgeol_thurgau_paired_v001/"
    "gold_interval_manifest_v001.jsonl"
)
SUSPICIOUS_RANGE = re.compile(r"(?mi)^\s*[&§$]\s*[-–—]\s*\d")
VIEW_BOXES = {
    "full": None,
    "roi_left_043": (0.02, 0.23, 0.43, 0.72),
    "roi_left_055": (0.02, 0.23, 0.55, 0.72),
}
PSM_VALUES = (3, 4, 6)


def render_pdf(pdf: Path, output_root: Path, dpi: int) -> list[Path]:
    executable = shutil.which("pdftoppm")
    if executable is None:
        raise RuntimeError("pdftoppm is required")
    completed = subprocess.run(
        [executable, "-png", "-r", str(dpi), str(pdf), str(output_root / "page")],
        text=True, capture_output=True, check=False,
    )
    pages = sorted(output_root.glob("page-*.png"))
    if completed.returncode != 0 or not pages:
        raise RuntimeError(f"pdftoppm failed for {pdf}: {completed.stderr.strip()}")
    return pages


def ocr_text(image: Path, psm: int) -> str:
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng", "--psm", str(psm)],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"tesseract failed for {image}: {completed.stderr.strip()}")
    return completed.stdout


def intervals(section) -> list[dict]:
    return [
        {
            "top_depth_m": float(top),
            "bottom_depth_m": float(bottom),
            "thickness_m": float(bottom - top),
        }
        for top, bottom in section
    ]


def section_key(section) -> tuple[tuple[float, float], ...]:
    return tuple((float(top), float(bottom)) for top, bottom in section)


def contains_section(container, subset) -> bool:
    return all(pair in set(container) for pair in subset)


def contiguous_from_zero(section) -> bool:
    if not section or float(section[0][0]) != 0.0:
        return False
    return all(
        float(top) < float(bottom)
        and (index == 0 or float(section[index - 1][1]) == float(top))
        for index, (top, bottom) in enumerate(section)
    )


def select_v2_candidate(first_section, peer_section, counts):
    """Require peer/high-resolution evidence for a complete zero-based sequence."""
    peer = section_key(peer_section)
    first = section_key(first_section)
    if not contiguous_from_zero(peer) or peer == first:
        return None, "peer_not_complete_or_unchanged"
    exact_support = counts.get(peer, 0)
    if exact_support >= 2:
        return peer, "peer_exact_highres_consensus"

    # Complementary evidence is allowed when first-pass and repeated high-res
    # sections jointly cover every peer interval without introducing an
    # interval outside the peer sequence. This handles a split table where one
    # reader sees the shallow row and another repeatedly sees the deeper row.
    peer_intervals = set(peer)
    if first and not set(first).issubset(peer_intervals):
        return None, "first_pass_conflicts_with_peer"
    covered = set(first)
    for section, support in counts.items():
        if support >= 2 and set(section).issubset(peer_intervals):
            covered.update(section)
    if covered == peer_intervals:
        return peer, "peer_complementary_highres_consensus"
    return None, "insufficient_peer_corroboration"


def exact_document(reference: list[dict], prediction: list[dict]) -> bool:
    matches, missing, extra = match_intervals_by_boundaries(reference, prediction, 0.05)
    return len(matches) == len(reference) == len(prediction) and not missing and not extra


def metric_dicts(references, predictions) -> dict:
    return {
        name: value.to_dict()
        for name, value in boundary_matched_interval_metrics(
            references, predictions, tolerance_m=0.05,
        ).items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--evaluation-manifest", type=Path, required=True)
    parser.add_argument("--development-manifest", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--evaluation-role", choices=("development", "heldout"), default="heldout",
    )
    parser.add_argument(
        "--dataset-version", default="swissgeol_incremental_authoritative_interval_heldout",
    )
    parser.add_argument(
        "--split-version", default="v001_development_disjoint_incremental_v002_evaluation",
    )
    parser.add_argument("--policy-version", choices=("v1", "v2"), default="v1")
    arguments = parser.parse_args()

    evaluation_rows = [
        json.loads(line)
        for line in arguments.evaluation_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    development_rows = [
        json.loads(line)
        for line in arguments.development_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not evaluation_rows:
        raise ValueError("held-out evaluation manifest is empty")
    development_ids = {row["record_id"] for row in development_rows}
    evaluation_ids = {row["record_id"] for row in evaluation_rows}
    overlap = development_ids & evaluation_ids
    if overlap:
        raise ValueError(f"development/evaluation record overlap: {sorted(overlap)}")

    sanitized_inputs = []
    for row in evaluation_rows:
        pdf = Path(row["pdf_path"])
        if file_sha256(pdf) != row["pdf_sha256"]:
            raise ValueError(f"PDF hash mismatch: {pdf}")
        sanitized_inputs.append({
            "record_id": row["record_id"],
            "borehole_id": row["borehole_id"],
            "pdf_path": str(pdf),
            "pdf_sha256": row["pdf_sha256"],
        })

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.strip()
    tesseract_version = subprocess.run(
        ["tesseract", "--version"], text=True, capture_output=True, check=True,
    ).stdout.splitlines()[0]
    started = datetime.now(timezone.utc)
    trigger_config = ["empty_interval_section", "suspicious_numeric_range", "reader_disagreement"]
    if arguments.policy_version == "v2":
        trigger_config.append("incomplete_top_boundary")
    acceptance_config = (
        {
            "peer_sequence_must_start_at_zero": True,
            "peer_sequence_must_be_contiguous": True,
            "minimum_exact_highres_support": 2,
            "allow_complementary_first_and_highres_coverage": True,
            "candidate_must_equal_trigger_reader_sequence": True,
        }
        if arguments.policy_version == "v2"
        else {
            "minimum_identical_reader_support": 2,
            "unique_top_support_required": True,
            "baseline_intervals_must_be_preserved": True,
        }
    )
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": arguments.dataset_version,
        "split_version": arguments.split_version,
        "model": f"constraint_triggered_multiview_tesseract_reread_{arguments.policy_version}",
        "model_revision": tesseract_version,
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version(), "tesseract": tesseract_version},
        "config": {
            "ground_truth_sha256": file_sha256(arguments.evaluation_manifest),
            "development_manifest_sha256": file_sha256(arguments.development_manifest),
            "prediction_reference_conditioning": "none",
            "first_pass": {"render_dpi": 250, "psm": 3},
            "trigger_reader": {"render_dpi": 250, "psm": 4},
            "triggers": trigger_config,
            "reread": {
                "render_dpi": 350,
                "view_boxes_normalized": VIEW_BOXES,
                "psm_values": list(PSM_VALUES),
            },
            "acceptance": acceptance_config,
            "reference_blinded_decision_policy": True,
            "evaluation_role": arguments.evaluation_role,
            "policy_version": arguments.policy_version,
        },
        "started_utc": started.isoformat(),
    })
    case_root = run / "case_artifacts"
    case_root.mkdir()
    frozen_predictions = []
    wall_started = time.perf_counter()

    for source in sanitized_inputs:
        case_started = time.perf_counter()
        record_root = case_root / source["record_id"]
        record_root.mkdir()
        with tempfile.TemporaryDirectory(prefix="geologparser-reread-first-") as temporary:
            pages = render_pdf(Path(source["pdf_path"]), Path(temporary), 250)
            first_text = "\n\n".join(ocr_text(page, 3) for page in pages)
            peer_text = "\n\n".join(ocr_text(page, 4) for page in pages)
        first_section = choose_interval_section(first_text)
        peer_section = choose_interval_section(peer_text)
        triggers = []
        if not first_section:
            triggers.append("empty_interval_section")
        if SUSPICIOUS_RANGE.search(first_text):
            triggers.append("suspicious_numeric_range")
        if section_key(first_section) != section_key(peer_section):
            triggers.append("reader_disagreement")
        if arguments.policy_version == "v2" and first_section and first_section[0][0] > 0:
            triggers.append("incomplete_top_boundary")
        (record_root / "first_pass_psm3.txt").write_text(first_text, encoding="utf-8")
        (record_root / "first_pass_psm4.txt").write_text(peer_text, encoding="utf-8")

        candidate_rows = []
        if triggers:
            with tempfile.TemporaryDirectory(prefix="geologparser-reread-highres-") as temporary:
                pages = render_pdf(Path(source["pdf_path"]), Path(temporary), 350)
                if len(pages) != 1:
                    raise ValueError("held-out reread pilot currently requires one-page PDFs")
                page = Image.open(pages[0])
                for view_name, box in VIEW_BOXES.items():
                    image = page if box is None else page.crop((
                        int(page.width * box[0]), int(page.height * box[1]),
                        int(page.width * box[2]), int(page.height * box[3]),
                    ))
                    image_path = record_root / f"{view_name}.png"
                    image.save(image_path)
                    for psm in PSM_VALUES:
                        text = ocr_text(image_path, psm)
                        text_path = record_root / f"{view_name}_psm{psm}.txt"
                        text_path.write_text(text, encoding="utf-8")
                        section = choose_interval_section(text)
                        if section:
                            candidate_rows.append({
                                "reader": f"350dpi:{view_name}:psm{psm}",
                                "section": section_key(section),
                            })
        counts = Counter(row["section"] for row in candidate_rows)
        accepted = None
        acceptance_reason = None
        decision = "KEEP_FIRST_PASS"
        if arguments.policy_version == "v2":
            accepted, acceptance_reason = select_v2_candidate(
                first_section, peer_section, counts,
            )
            if accepted is not None:
                decision = "ACCEPT_REREAD"
        else:
            eligible = {
                section: support
                for section, support in counts.items()
                if support >= 2 and (
                    not first_section or contains_section(section, section_key(first_section))
                )
            }
            ranked = sorted(
                eligible.items(), key=lambda item: (item[1], len(item[0]), item[0]), reverse=True,
            )
            if ranked:
                top_section, top_support = ranked[0]
                next_support = ranked[1][1] if len(ranked) > 1 else -1
                if top_support > next_support and top_section != section_key(first_section):
                    accepted = top_section
                    acceptance_reason = "v1_unique_supported_extension"
                    decision = "ACCEPT_REREAD"
        if triggers and accepted is None:
            decision = "NEEDS_REVIEW"
        final_section = accepted if accepted is not None else section_key(first_section)
        frozen_predictions.append({
            **source,
            "first_pass_intervals": intervals(first_section),
            "peer_intervals": intervals(peer_section),
            "triggers": triggers,
            "candidate_support": [
                {"intervals": intervals(section), "support": support}
                for section, support in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            ],
            "decision": decision,
            "acceptance_reason": acceptance_reason,
            "final_intervals": intervals(final_section),
            "latency_seconds": time.perf_counter() - case_started,
        })

    # References enter only after every decision is frozen above.
    references_by_id = {}
    for row in evaluation_rows:
        reference_path = Path(row["reference_path"])
        if file_sha256(reference_path) != row["reference_sha256"]:
            raise ValueError(f"reference hash mismatch: {reference_path}")
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        references_by_id[row["record_id"]] = sorted(
            [
                {
                    "top_depth_m": float(item["top_depth_m"]),
                    "bottom_depth_m": float(item["bottom_depth_m"]),
                    "thickness_m": float(item["thickness_m"]),
                }
                for item in reference["stratigraphy"]["intervals"]
            ],
            key=lambda item: (item["top_depth_m"], item["bottom_depth_m"]),
        )
    for row in frozen_predictions:
        row["reference_intervals"] = references_by_id[row["record_id"]]
        row["first_pass_exact"] = exact_document(
            row["reference_intervals"], row["first_pass_intervals"],
        )
        row["final_exact"] = exact_document(
            row["reference_intervals"], row["final_intervals"],
        )

    references = [row["reference_intervals"] for row in frozen_predictions]
    first_predictions = [row["first_pass_intervals"] for row in frozen_predictions]
    final_predictions = [row["final_intervals"] for row in frozen_predictions]
    accepted_rows = [row for row in frozen_predictions if row["decision"] == "ACCEPT_REREAD"]
    incorrect_first = [row for row in frozen_predictions if not row["first_pass_exact"]]
    correct_first = [row for row in frozen_predictions if row["first_pass_exact"]]
    successful = sum(not row["first_pass_exact"] and row["final_exact"] for row in accepted_rows)
    false_corrections = sum(row["first_pass_exact"] and not row["final_exact"] for row in accepted_rows)
    triggers_on_incorrect = sum(bool(row["triggers"]) for row in incorrect_first)
    triggers_on_correct = sum(bool(row["triggers"]) for row in correct_first)
    wall_seconds = time.perf_counter() - wall_started
    metrics = {
        "scope": (
            "authoritative-interval heldout constraint-rereading evaluation"
            if arguments.evaluation_role == "heldout"
            else "authoritative-interval development constraint-rereading evaluation"
        ),
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "comparison": "single_pass_vs_constraint_guided_reread",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "development_evaluation_overlap_count": 0,
        "document_count": len(frozen_predictions),
        "reference_interval_count": sum(len(row) for row in references),
        "first_pass": {
            "interval_metrics": metric_dicts(references, first_predictions),
            "document_full_exact_count": sum(row["first_pass_exact"] for row in frozen_predictions),
        },
        "constraint_reread": {
            "interval_metrics": metric_dicts(references, final_predictions),
            "document_full_exact_count": sum(row["final_exact"] for row in frozen_predictions),
        },
        "triggered_document_count": sum(bool(row["triggers"]) for row in frozen_predictions),
        "accepted_reread_count": len(accepted_rows),
        "needs_review_count": sum(row["decision"] == "NEEDS_REVIEW" for row in frozen_predictions),
        "correction_success_rate": {
            "value": successful / len(accepted_rows) if accepted_rows else None,
            "numerator": successful,
            "denominator": len(accepted_rows),
        },
        "false_correction_rate": {
            "value": false_corrections / len(accepted_rows) if accepted_rows else None,
            "numerator": false_corrections,
            "denominator": len(accepted_rows),
            "unit": "document_section_replacement",
        },
        "incorrect_document_trigger_recall": {
            "value": triggers_on_incorrect / len(incorrect_first) if incorrect_first else None,
            "numerator": triggers_on_incorrect,
            "denominator": len(incorrect_first),
        },
        "correct_document_trigger_rate": {
            "value": triggers_on_correct / len(correct_first) if correct_first else None,
            "numerator": triggers_on_correct,
            "denominator": len(correct_first),
        },
        "wall_time_seconds": wall_seconds,
        "latency_seconds_per_document_wall": wall_seconds / len(frozen_predictions),
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "evaluation_role": arguments.evaluation_role,
        "policy_version": arguments.policy_version,
        "selection_limitation": (
            f"{arguments.evaluation_role} records from the same canton/source family; "
            "source-agreement explicit-table selection; not cross-source or representative "
            "deployment evidence"
        ),
    }
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in frozen_predictions),
        encoding="utf-8",
    )
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    errors = []
    for row in frozen_predictions:
        _, missing, extra = match_intervals_by_boundaries(
            row["reference_intervals"], row["final_intervals"], 0.05,
        )
        errors.extend(
            {"record_id": row["record_id"], "error_type": "missing_interval", "index": index}
            for index in missing
        )
        errors.extend(
            {"record_id": row["record_id"], "error_type": "spurious_interval", "index": index}
            for index in extra
        )
    (run / "errors.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in errors), encoding="utf-8",
    )
    (run / "run.log").write_text(
        f"documents={len(frozen_predictions)}\nwall_seconds={wall_seconds:.6f}\nstatus=completed\n",
        encoding="utf-8",
    )
    write_artifact_manifest(run)
    print(run)


if __name__ == "__main__":
    main()
