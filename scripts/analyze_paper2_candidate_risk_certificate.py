#!/usr/bin/env python3
"""Quantify finite-sample risk bounds for the frozen California acceptance policy.

This is a secondary analysis of immutable, reference-blind policy decisions.  It
does not select a threshold, change a model, or convert two California sources
into a source-generalization claim.  It distinguishes action-level error risk
from document-level worsening risk, which have materially different effective
sample sizes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import argparse
import json
import math
from pathlib import Path
import platform
import subprocess
import time

from geologparser.experiment import create_run_directory
from geologparser.result_index import file_sha256, write_artifact_manifest
from geologparser.runtime_resources import peak_process_rss_kib


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RUNS = {
    "development_v001": ROOT / "results/2026-08-15/P2_CALIFORNIA_CANDIDATE_RISK_V002_DEV_V001_001",
    "development_v002": ROOT / "results/2026-08-15/P2_CALIFORNIA_CANDIDATE_RISK_V002_DEV_V002_001",
    "external_v004": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V004_CANDIDATE_RISK_PROSPECTIVE_FORMAL_001",
    "external_v005": ROOT / "results/2026-08-15/P2_CALIFORNIA_WCR_V005_CANDIDATE_RISK_EXTERNAL_FORMAL_001",
}


def zero_error_upper_bound(count: int, alpha: float) -> float | None:
    """Exact one-sided Clopper--Pearson upper bound when observed errors are zero."""
    if count <= 0:
        return None
    return 1.0 - alpha ** (1.0 / count)


def zero_error_target_p_value(count: int, target_risk: float) -> float | None:
    """P(X=0 | p=target_risk), used only for the stated iid Bernoulli assumption."""
    if count <= 0:
        return None
    return (1.0 - target_risk) ** count


def group_summary(name: str, metrics: list[dict]) -> dict:
    action_count = sum(int(row["accepted_correction_actions"]) for row in metrics)
    action_errors = sum(int(row["accepted_incorrect_additions"]) for row in metrics)
    document_count = sum(int(row["accepted_correction_document_count"]) for row in metrics)
    document_errors = sum(int(row["document_outcomes"]["worsened"]) for row in metrics)
    if action_errors or document_errors:
        raise ValueError("this certificate implementation only supports the observed zero-error cohorts")
    return {
        "cohort": name,
        "action_level": {
            "accepted_actions": action_count,
            "observed_incorrect_actions": action_errors,
            "observed_fcr": 0.0 if action_count else None,
            "one_sided_95pct_upper_fcr": zero_error_upper_bound(action_count, 0.05),
            "one_sided_99pct_upper_fcr": zero_error_upper_bound(action_count, 0.01),
            "p_zero_errors_if_true_fcr_at_least_5pct": zero_error_target_p_value(action_count, 0.05),
            "p_zero_errors_if_true_fcr_at_least_2pct": zero_error_target_p_value(action_count, 0.02),
        },
        "document_level": {
            "accepted_documents": document_count,
            "observed_worsened_documents": document_errors,
            "observed_worsening_rate": 0.0 if document_count else None,
            "one_sided_95pct_upper_worsening_rate": zero_error_upper_bound(document_count, 0.05),
            "one_sided_99pct_upper_worsening_rate": zero_error_upper_bound(document_count, 0.01),
            "p_zero_worsenings_if_true_rate_at_least_5pct": zero_error_target_p_value(document_count, 0.05),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--experiment-id",
        default="P2_CALIFORNIA_CANDIDATE_RISK_CERTIFICATE_001",
    )
    arguments = parser.parse_args()
    started = datetime.now(timezone.utc)
    wall = time.perf_counter()

    loaded = {
        name: json.loads((path / "metrics.json").read_text(encoding="utf-8"))
        for name, path in DEFAULT_RUNS.items()
    }
    source_runs = {
        name: json.loads((path / "run.json").read_text(encoding="utf-8"))
        for name, path in DEFAULT_RUNS.items()
    }
    policy_hashes = {row["config"]["policy_config_sha256"] for row in source_runs.values()}
    semantic_rules = {
        (
            row["model"], row["model_revision"],
            float(row["config"]["minimum_node_score"]),
            bool(row["config"]["preserve_all_raw_intervals"]),
            bool(row["config"]["reject_if_positive_overlap_with_selected"]),
        )
        for row in source_runs.values()
    }
    if len(semantic_rules) != 1:
        raise ValueError("certificate requires identical model/revision/rule semantics across all cohorts")

    cohorts = [
        group_summary("development", [loaded["development_v001"], loaded["development_v002"]]),
        group_summary("external_v004", [loaded["external_v004"]]),
        group_summary("external_v005", [loaded["external_v005"]]),
        group_summary("external_pooled_v004_v005", [loaded["external_v004"], loaded["external_v005"]]),
    ]
    external = cohorts[-1]
    decision = {
        "action_level_5pct_risk": (
            "SUPPORTED_UNDER_IID_ACTION_ASSUMPTION"
            if external["action_level"]["one_sided_95pct_upper_fcr"] <= 0.05
            else "NOT_SUPPORTED"
        ),
        "action_level_2pct_risk": (
            "SUPPORTED_UNDER_IID_ACTION_ASSUMPTION"
            if external["action_level"]["one_sided_95pct_upper_fcr"] <= 0.02
            else "NOT_SUPPORTED"
        ),
        "document_level_5pct_worsening": (
            "SUPPORTED_UNDER_IID_DOCUMENT_ASSUMPTION"
            if external["document_level"]["one_sided_95pct_upper_worsening_rate"] <= 0.05
            else "NO_GO_INSUFFICIENT_ACCEPTED_DOCUMENTS"
        ),
    }
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    run = create_run_directory(arguments.results_root, {
        "experiment_id": arguments.experiment_id,
        "git_commit": commit,
        "date": date.today().isoformat(),
        "dataset_version": "california_wcr_gold_v001_v002_v004_v005_frozen_policy_outcomes",
        "split_version": "secondary_action_risk_analysis_no_threshold_selection",
        "model": "california_addition_only_high_confidence_v002",
        "model_revision": "risk_certificate_v001",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "processor": platform.processor(), "gpu_used": False},
        "software": {"python": platform.python_version()},
        "config": {
            "policy_config_sha256_by_source": {
                name: row["config"]["policy_config_sha256"] for name, row in source_runs.items()
            },
            "policy_semantic_rule": {
                "model": next(iter(semantic_rules))[0],
                "model_revision": next(iter(semantic_rules))[1],
                "minimum_node_score": next(iter(semantic_rules))[2],
                "preserve_all_raw_intervals": next(iter(semantic_rules))[3],
                "reject_if_positive_overlap_with_selected": next(iter(semantic_rules))[4],
            },
            "policy_hash_note": "v004/v005 use a later config-file hash, but every evaluated run has identical policy id, model revision, threshold, preserve-raw and non-overlap rule semantics",
            "source_runs": {name: str(path.relative_to(ROOT)) for name, path in DEFAULT_RUNS.items()},
            "source_metric_sha256": {
                name: file_sha256(path / "metrics.json") for name, path in DEFAULT_RUNS.items()
            },
            "source_run_sha256": {
                name: file_sha256(path / "run.json") for name, path in DEFAULT_RUNS.items()
            },
            "reference_blinded_policy_decisions": True,
            "statistical_method": "exact one-sided Clopper-Pearson zero-error upper bound",
            "assumption": "iid Bernoulli actions/documents within reported cohort; clustering and source shift are not eliminated",
        },
        "started_utc": started.isoformat(),
    })
    metrics = {
        "scope": "secondary frozen-policy action-risk certification",
        "comparison": "frozen_candidate_risk_policy_action_vs_document_risk_bounds",
        "reference_ground_truth_tier": "GOLD_PUBLISHED_MANUAL_TRANSCRIPTION",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "policy_status": "frozen before v004/v005 evaluation",
        "cohorts": cohorts,
        "decision": decision,
        "interpretation": (
            "The external action-level cohort has enough zero-error actions to reject a 5% FCR "
            "at the one-sided 95% level under an iid-action assumption. It cannot certify a 2% "
            "FCR target, and the accepted-document cohort is too small to certify a 5% document "
            "worsening target. These are finite-sample confidence bounds, not cross-source guarantees."
        ),
        "limitations": [
            "v004 and v005 are content-disjoint California evaluations, not independent source families",
            "zero-error Clopper-Pearson bound assumes independent Bernoulli units; document clustering can invalidate action-level independence",
            "no BGS, Swissgeol, or BGS v003 outcome is used to choose the policy or estimate a universal deployment guarantee",
            "this analysis does not improve extraction recall or unseen-template coverage",
        ],
        "wall_time_seconds": time.perf_counter() - wall,
        "peak_process_rss_kib": peak_process_rss_kib(),
    }
    (run / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in cohorts),
        encoding="utf-8",
    )
    (run / "errors.jsonl").write_text("", encoding="utf-8")
    (run / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run / "run.log").write_text(
        f"started_utc={started.isoformat()}\nstatus=completed\npolicy=frozen\n", encoding="utf-8"
    )
    write_artifact_manifest(run)
    print(run)
    print(json.dumps({"external": external, "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
