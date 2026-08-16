#!/usr/bin/env python3
"""Materialize the immutable core-file bundle for the consumed BGS v003 run."""

from __future__ import annotations

import json
from pathlib import Path

from geologparser.result_index import write_artifact_manifest


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "experiments/paper2/analysis/bgs_v003_v028_routed_external_final.json"
MANIFEST = ROOT / "datasets/manifests/bgs_offshore_gold_v003.jsonl"
DEST = ROOT / "results/2026-08-16/P2_BGS_V028_ROUTED_EXTERNAL_V003_FINAL"


def main() -> None:
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    DEST.mkdir(parents=True, exist_ok=True)

    overall = analysis["overall"]
    run = {
        "experiment_id": "P2_BGS_V028_ROUTED_EXTERNAL_V003_FINAL",
        "git_commit": "0c28eddf121c7e36925b13ada7f6043c2e9c3c23",
        "date": "2026-08-16",
        "dataset_version": "bgs_offshore_gold_v003",
        "split_version": "one_time_frozen_external_v003",
        "model": analysis["method_version"],
        "model_revision": "v028",
        "prompt_version": "not_applicable",
        "seed": 0,
        "hardware": {"device": "cpu", "gpu_used": False},
        "software": {"python": "3.10.12"},
        "config": {
            "ground_truth_sha256": analysis["manifest_sha256"],
            "reference_blinding": analysis["reference_blinding"],
            "post_external_policy": "no tuning; any method change demotes the set to validation",
            "protocol_deviation": "hash_only_manifest_access_before_preregistered_freeze_commit; no semantic inspection or tuning",
        },
    }
    metrics = {
        "scope": "one-time frozen unseen-source external failure evaluation",
        "data_status": "real_bgs_v003_external_source",
        "reference_ground_truth_tier": "GOLD_AUTHORITATIVE_SOURCE_AGREEMENT",
        "comparison": "frozen_v028_routed_parser_vs_authoritative_boundaries",
        "prediction_reference_conditioning": "none",
        "reference_blinded_decision_policy": True,
        "human_ground_truth_evidence": False,
        "document_count": analysis["document_count"],
        "page_count": analysis["page_count"],
        "reference_interval_count": overall["interval"]["false_negative"] + overall["interval"]["true_positive"],
        "reference_boundary_count": overall["boundary"]["false_negative"] + overall["boundary"]["true_positive"],
        "boundary_f1": overall["boundary"]["f1"],
        "interval_f1": overall["interval"]["f1"],
        "boundary_precision": overall["boundary"]["precision"],
        "boundary_recall": overall["boundary"]["recall"],
        "coverage": 0.0,
        "critical_numerical_error_rate": 0.0,
        "false_positive_count": overall["boundary"]["false_positive"],
        "route": "abstain_unsupported_family",
        "status": "completed_external_evaluation",
        "limitations": "single record and one unseen page family; full abstention is safe but operationally unusable",
    }
    predictions = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in analysis["predictions"]) + "\n"
    errors = json.dumps({"error_count": 0, "note": "no emitted false-positive boundary; all pages abstained"}, ensure_ascii=False) + "\n"
    (DEST / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DEST / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DEST / "predictions.jsonl").write_text(predictions, encoding="utf-8")
    (DEST / "errors.jsonl").write_text(errors, encoding="utf-8")
    (DEST / "run.log").write_text(
        "Frozen BGS v003 external evaluation. No post-result tuning.\n"
        "Route: abstain_unsupported_family; coverage=0; false positives=0.\n",
        encoding="utf-8",
    )
    write_artifact_manifest(DEST)
    print(DEST)


if __name__ == "__main__":
    main()
