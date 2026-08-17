"""Manuscript-facing tables for the post-review statistical reanalysis.

The renderers deliberately consume only versioned analysis JSON.  They keep
evidence tiers and statistical units in the table itself so that results from
manual transcription Gold, source-agreement references, and audit material
cannot be visually conflated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ratio(value: float | None, digits: int = 3) -> str:
    return "--" if value is None else f"{value:.{digits}f}"


def _ci(values: list[float]) -> str:
    return f"[{values[0]:.3f}, {values[1]:.3f}]"


def paper1_major_revision_table(analysis_path: Path) -> str:
    analysis = _load(analysis_path)
    labels = {
        "v001": "California v001",
        "v002_external": "California v002",
        "v003_prospective": "California v003",
        "v004_prospective": "California v004",
        "v005_external": "California v005",
    }
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "# Paper I major-revision tables",
        "",
        "## Five California cohorts",
        "",
        "Evidence tier for every row: **Published manual transcription Gold**. "
        "The statistical unit for confidence intervals is the document; pooled interval counts are descriptive.",
        "",
        "| Cohort | Documents | Reference intervals | Predicted | Matched | Precision (95% CI) | Recall (95% CI) | F1 (95% CI) | Zero output | Boundary exact | Full-record exact | Median document recall |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in labels.items():
        cohort = analysis["freezes"][key]
        metrics = cohort["rapidocr_document_cluster_metrics"]
        diagnostics = cohort["rapidocr_document_diagnostics"]
        ci = metrics["bootstrap_percentile_95_ci"]
        count = diagnostics["document_count"]
        lines.append(
            f"| {label} | {count} | {metrics['reference']} | {metrics['predicted']} | "
            f"{metrics['matched']} | {_ratio(metrics['precision'])} {_ci(ci['precision'])} | "
            f"{_ratio(metrics['recall'])} {_ci(ci['recall'])} | "
            f"{_ratio(metrics['f1'])} {_ci(ci['f1'])} | "
            f"{diagnostics['zero_output_document_count']}/{count} | "
            f"{diagnostics['boundary_exact_document_count']}/{count} | "
            f"{diagnostics['full_exact_document_count']}/{count} | "
            f"{_ratio(diagnostics['per_document_recall']['median'])} |"
        )
    lines.extend([
        "",
        "The confidence intervals are 20,000-repetition percentile document-cluster bootstraps. "
        "Exact-record columns prevent high conditional precision from hiding whole-record omission.",
        "",
    ])
    return "\n".join(lines)


def _ablation_metric(cohort: Mapping[str, Any], variant: str, name: str) -> float:
    return float(cohort["metrics"][variant][name]["value"])


def paper2_major_revision_tables(ablation_path: Path, risk_path: Path) -> str:
    ablation = _load(ablation_path)
    risk = _load(risk_path)
    variants = [
        ("raw_parser", "Raw parser"),
        ("candidate_pool_without_sequence", "Eligible pool, no sequence"),
        ("monotonic_sequence", "+ monotonic sequence"),
        ("continuity_sequence", "+ continuity / zero-origin"),
        ("column_stable_without_semantic_bonus", "+ column stability, no term bonus"),
        ("complete_sequence", "Complete archived score"),
    ]
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "# Paper II major-revision tables",
        "",
        "## Same-candidate-pool sequence ablation",
        "",
        "Evidence tier: **Published manual transcription Gold**. All variants use identical documents, "
        "positioned candidate pools, matcher, and tolerance; the bootstrap unit is the document.",
        "",
        "| Variant | v004 P / R / F1 (95% CI) | v004 FCR | v005 P / R / F1 (95% CI) | v005 FCR |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, label in variants:
        cells = []
        fcrs = []
        for freeze in ("v004", "v005"):
            cohort = ablation["freezes"][freeze]
            precision = _ablation_metric(cohort, key, "interval_precision")
            recall = _ablation_metric(cohort, key, "interval_recall")
            f1 = _ablation_metric(cohort, key, "interval_f1")
            interval = cohort["document_cluster_f1"][key]["document_cluster_percentile_95_ci"]
            cells.append(f"{precision:.3f} / {recall:.3f} / {f1:.3f} {_ci(interval)}")
            safety = cohort["correction_safety"].get(key)
            fcrs.append("--" if safety is None else _ratio(safety["false_correction_rate"]))
        lines.append(f"| {label} | {cells[0]} | {fcrs[0]} | {cells[1]} | {fcrs[1]} |")

    combined = risk["combined_confirmatory"]
    lines.extend([
        "",
        "## Document-level risk and net utility",
        "",
        "Evidence tier: **Published manual transcription Gold**. The primary safety unit is the document; "
        "the iid-action bound is retained only as a secondary diagnostic.",
        "",
        "| Cohort | Policy | Net additional matches / 100 documents | Net change in incorrect predictions | Worsened documents (document F1) | Accepted documents | Review/abstain documents |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for freeze in ("v004", "v005"):
        cohort = risk["freezes"][freeze]
        utility = cohort["net_utility"]
        review = cohort["review_and_coverage"]
        lines.extend([
            f"| {freeze} | Unselective sequence | {utility['correct_intervals_added_per_100_documents']['unselective']:.1f} | "
            f"{utility['unselective_erroneous_prediction_gain']} | {utility['unselective_worsened_document_count']} | "
            f"{review['documents_with_changed_candidate_sequence']} | 0 |",
            f"| {freeze} | Addition-only risk policy | {utility['correct_intervals_added_per_100_documents']['risk']:.1f} | "
            f"{utility['risk_erroneous_prediction_gain']} | {utility['risk_worsened_document_count']} | "
            f"{review['accepted_document_count']} | {review['review_or_abstain_document_count']} |",
        ])
    lines.extend([
        "",
        f"Across 200 documents, the addition-only policy accepted {combined['accepted_action_count']} actions in "
        f"{combined['accepted_document_count']} documents, observed {combined['observed_worsened_document_count']} worsened documents, "
        f"and retained {combined['review_or_abstain_document_count']} changed-sequence documents for review or abstention. "
        f"The one-sided 95% zero-event upper bound is {combined['document_level_one_sided_95_upper_bound']:.4f} per accepted document; "
        f"the secondary iid-action bound is {combined['action_level_one_sided_95_upper_bound_iid_assumption']:.4f}.",
        "",
    ])
    return "\n".join(lines)


def _aggregate(comparison: Mapping[str, Any], variant: str) -> Mapping[str, Any]:
    return comparison[variant]["aggregate"]


def paper3_major_revision_tables(analysis_path: Path) -> str:
    analysis = _load(analysis_path)
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "# Paper III major-revision tables",
        "",
        "## Full-support and strict matched-subset diagnostics",
        "",
        "Evidence tier: **Source-agreement reference**. These are surface and volume diagnostics, not validated geological models.",
        "",
        "| Estimand | Variant | Documents | Mean thickness MAE (m) | Relative absolute volume error | Mean top support | Mean bottom support | Negative-thickness layers |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for estimand, comparison, docs in (
        ("Full support", analysis["full_support_comparison"], analysis["document_count"]),
        ("Matched accepted subset", analysis["matched_subset_comparison"], analysis["risk_accepted_document_count"]),
    ):
        for variant in ("raw", "reread", "risk"):
            aggregate = _aggregate(comparison, variant)
            lines.append(
                f"| {estimand} | {variant} | {docs} | {aggregate['mean_thickness_mae_m']:.3f} | "
                f"{aggregate['relative_absolute_volume_error']:.4f} | {aggregate['mean_top_support']:.3f} | "
                f"{aggregate['mean_bottom_support']:.3f} | {aggregate['layers_with_negative_thickness']} |"
            )

    support = {
        row["variant"]: row for row in analysis["spatial_support"] if row["boundary_index"] == 1
    }
    lines.extend([
        "",
        "## First-boundary spatial support",
        "",
        "| Variant | Effective points | Point coverage | Hull-area ratio | Mean nearest-neighbour distance (m) | Mean grid-to-observation distance (m) |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for variant in ("raw", "reread", "risk"):
        row = support[variant]
        lines.append(
            f"| {variant} | {row['effective_point_count']}/{row['reference_point_count']} | "
            f"{row['point_coverage']:.3f} | {row['convex_hull_area_ratio']:.3f} | "
            f"{row['nearest_neighbour_distance_m']['mean']:.1f} | "
            f"{row['grid_to_nearest_observation_distance_m']['mean']:.1f} |"
        )

    lines.extend([
        "",
        "## Accepted versus rejected document diagnostics",
        "",
        "| Risk-router group | Documents | Reference boundaries | Raw available | Raw missing | Raw aligned MAE (m) | Raw exact documents | Hull-area ratio | Mean nearest-neighbour distance (m) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for group_name in ("accepted", "rejected"):
        row = analysis["acceptance_group_diagnostics"][group_name]
        lines.append(
            f"| {group_name} | {row['document_count']} | {row['reference_boundary_count']} | "
            f"{row['raw_available_boundary_count']} | {row['raw_missing_boundary_count']} | "
            f"{row['raw_order_aligned_boundary_mae_m']:.3f} | {row['raw_exact_document_count']}/{row['document_count']} | "
            f"{row['convex_hull_area_ratio_to_all_records']:.3f} | {row['nearest_neighbour_distance_m']['mean']:.1f} |"
        )

    sensitivity: dict[tuple[str, str], list[float]] = {}
    for row in analysis["idw_parameter_sensitivity"]:
        domain = row["domain"]
        for variant in ("raw", "reread", "risk"):
            value = row["variants"][variant]["relative_absolute_volume_error"]
            if value is not None:
                sensitivity.setdefault((domain, variant), []).append(float(value))
    lines.extend([
        "",
        "## IDW and leave-one-borehole-out sensitivity",
        "",
        "| Domain | Variant | Relative volume-error range across IDW settings | Default LOO n | Default LOO MAE (m) |",
        "|---|---|---:|---:|---:|",
    ])
    default_loo = {
        row["domain"]: row for row in analysis["leave_one_borehole_out"]
        if row["power"] == 2.0 and row["neighbours"] == "all"
    }
    domains = (
        ("Full reference", "full_reference_hull", "all_reference_targets"),
        ("Matched accepted", "matched_accepted_hull", "matched_accepted_targets"),
    )
    for label, sensitivity_domain, loo_domain in domains:
        loo = default_loo[loo_domain]["variants"]
        for variant in ("reference", "raw", "reread", "risk"):
            values = sensitivity.get((sensitivity_domain, variant), [])
            volume_range = "--" if not values else f"{min(values):.3f}–{max(values):.3f}"
            lines.append(
                f"| {label} | {variant} | {volume_range} | "
                f"{loo[variant]['absolute_error_m']['count']} | {loo[variant]['absolute_error_m']['mean']:.2f} |"
            )
    lines.extend(["", "## Default LOO by ordered boundary", ""])
    lines.extend([
        "| Domain | Variant | B1 n / MAE (m) | B2 n / MAE (m) | B3 n / MAE (m) | B4 n / MAE (m) |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for label, _, loo_domain in domains:
        loo = default_loo[loo_domain]["variants"]
        for variant in ("reference", "raw", "reread", "risk"):
            cells = []
            for boundary in loo[variant]["by_boundary"][:4]:
                metric = boundary["absolute_error_m"]
                mean_text = "--" if metric["mean"] is None else f"{metric['mean']:.2f}"
                cells.append(f"{metric['count']} / {mean_text}")
            lines.append(f"| {label} | {variant} | " + " | ".join(cells) + " |")

    lines.extend([
        "",
        "## Leave-one-borehole-out volume jackknife",
        "",
        "| Domain | Variant | Replicates | Relative volume error, mean [min, max] | Thickness MAE, mean [min, max] (m) |",
        "|---|---|---:|---:|---:|",
    ])
    for label, key in (("Full support", "full_support"), ("Matched accepted", "matched_accepted_subset")):
        jackknife = analysis["volume_jackknife"][key]
        for variant in ("raw", "reread", "risk"):
            volume = jackknife["variants"][variant]["relative_absolute_volume_error"]
            thickness = jackknife["variants"][variant]["mean_thickness_mae_m"]
            lines.append(
                f"| {label} | {variant} | {jackknife['held_out_borehole_count']} | "
                f"{volume['mean']:.4f} [{volume['minimum']:.4f}, {volume['maximum']:.4f}] | "
                f"{thickness['mean']:.2f} [{thickness['minimum']:.2f}, {thickness['maximum']:.2f}] |"
            )
    lines.extend([
        "",
        "The full-support and matched-subset estimands answer different questions. The matched subset shows that "
        "risk-aware and reread inputs are identical after acceptance; the apparent full-support risk advantage is therefore a selection/support effect.",
        "",
    ])
    return "\n".join(lines)
