#!/usr/bin/env python3
"""Build the four integrated Computers & Geosciences main figures.

The figures deliberately use the frozen publication-analysis JSON files rather
than re-running or tuning any model.  The script is deterministic and writes a
small manifest containing the source hashes used for each panel.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures"
MODERN = ROOT / "experiments/paper1/analysis/modern_vlm_statistics_v001.json"
ASSURANCE = ROOT / "experiments/paper2/analysis/vlm_proposal_assurance_v001.json"
SPATIAL = ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d8dee9", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def fig1() -> None:
    fig, ax = plt.subplots(figsize=(13.0, 4.8), dpi=180)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    nodes = [
        (0.03, 0.42, 0.16, 0.28, "Modern VLM proposal", "high-recall\nimage → intervals", "#dbeafe"),
        (0.235, 0.42, 0.16, 0.28, "Independent evidence", "positioned values\npage + bbox", "#dcfce7"),
        (0.44, 0.42, 0.16, 0.28, "Deterministic checks", "units · order\ncolumn ownership", "#fef3c7"),
        (0.645, 0.55, 0.14, 0.22, "ACCEPT", "auditable row", "#bbf7d0"),
        (0.645, 0.28, 0.14, 0.22, "REVIEW", "raw proposal +\nreason preserved", "#fee2e2"),
        (0.84, 0.42, 0.14, 0.28, "Downstream", "support mask →\nsurface / volume", "#e0e7ff"),
    ]
    for x, y, w, h, title, body, color in nodes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                             linewidth=1.2, edgecolor="#334155", facecolor=color)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=11,
                fontweight="bold", color="#0f172a")
        ax.text(x + w / 2, y + h * 0.34, body, ha="center", va="center", fontsize=9,
                color="#334155")
    arrows = [
        ((0.19, 0.56), (0.235, 0.56)), ((0.395, 0.56), (0.44, 0.56)),
        ((0.60, 0.56), (0.645, 0.66)), ((0.60, 0.56), (0.645, 0.39)),
        ((0.785, 0.66), (0.84, 0.56)), ((0.785, 0.39), (0.84, 0.56)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                     linewidth=1.3, color="#475569"))
    ax.text(0.5, 0.91, "Provenance-grounded assurance is a decision layer, not a second generative answer",
            ha="center", fontsize=13, fontweight="bold", color="#0f172a")
    ax.text(0.5, 0.06, "The immutable VLM proposal remains available even when the system abstains.",
            ha="center", fontsize=9.5, color="#475569")
    fig.tight_layout()
    fig.savefig(OUT / "F1_trustworthy_framework.png", bbox_inches="tight")
    plt.close(fig)


def fig2() -> None:
    d = load(MODERN)
    keys = [value for value in d["analyses"].values() if "CALIFORNIA" in value["experiment_id"]]
    keys.sort(key=lambda x: int(x["cohort"].split("v")[1]))
    cohorts = [x["cohort"].replace("California v", "v") for x in keys]
    qwen = [x["document_cluster_metrics"]["f1"] for x in keys]
    rapid = [x["paired_against_frozen_rapidocr"]["right"]["f1"] for x in keys]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.6), dpi=180,
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    x = np.arange(len(cohorts))
    width = 0.36
    ax1.bar(x - width / 2, qwen, width, color="#2563eb", label="Qwen3.8-27B-FP8")
    ax1.bar(x + width / 2, rapid, width, color="#94a3b8", label="RapidOCR positioned")
    ax1.set_ylim(0, 1.0)
    ax1.set_ylabel("Boundary-pair interval F1")
    ax1.set_xticks(x, cohorts)
    ax1.set_title("Five record-disjoint California cohorts", fontweight="bold")
    ax1.legend(
        frameon=False, fontsize=8, loc="upper center", ncol=2,
        bbox_to_anchor=(0.5, -0.14),
    )
    style(ax1)
    for i, v in enumerate(qwen):
        ax1.text(i - width / 2, v + 0.025, f"{v:.3f}", ha="center", fontsize=8, color="#1d4ed8")
    ax2_labels = ["Swissgeol\nQwen", "Swissgeol\nRapidOCR", "Swissgeol\nTesseract", "BGS\nRapidOCR", "BGS\nTesseract", "Raft River\nRapidOCR"]
    ax2_values = [0.576923, 0.679, 0.857, 0.0379, 0.0405, 1.000]
    colors = ["#2563eb", "#94a3b8", "#64748b", "#cbd5e1", "#cbd5e1", "#64748b"]
    x2 = np.arange(len(ax2_labels))
    ax2.bar(x2, ax2_values, color=colors)
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel("Boundary-pair interval F1")
    ax2.set_xticks(x2, ax2_labels, fontsize=8)
    ax2.set_title("Source-shift panels (tiered evidence)", fontweight="bold")
    style(ax2)
    for i, v in enumerate(ax2_values):
        ax2.text(i, min(v + 0.035, 0.97), f"{v:.3f}", ha="center", fontsize=8)
    fig.suptitle("High familiar-source accuracy does not imply transport", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(OUT / "F2_vlm_source_shift.png", bbox_inches="tight")
    plt.close(fig)


def fig3() -> None:
    d = load(ASSURANCE)
    rows = {row["cohort"]: row for row in d["analyses"]}
    names = ["v001\ndev", "v002\nvalidation", "v003\nheld-out"]
    point_labels = ["dev", "validation", "held-out"]
    keys = ["California v001", "California v002", "California v003"]
    precision = [rows[k]["point_estimates"]["accepted_precision"] for k in keys]
    coverage = [rows[k]["point_estimates"]["accepted_coverage"] for k in keys]
    raw_p = [rows[k]["point_estimates"]["raw_precision"] for k in keys]
    complete = [rows[k]["complete_document_auto_acceptance"]["value"] for k in keys]
    heldout_metrics = load(ROOT / rows[keys[-1]]["result_path"] / "metrics.json")
    proposals = heldout_metrics["proposal_count"]
    accepted = heldout_metrics["accepted_proposal_coverage"]["numerator"]
    endpoint_anchor = heldout_metrics["same_page_numeric_anchor_coverage"]
    both_anchors = heldout_metrics["complete_interval_numeric_anchor_coverage"]
    top_anchor = heldout_metrics["top_numeric_anchor_coverage"]
    bottom_anchor = heldout_metrics["bottom_numeric_anchor_coverage"]
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.6, 4.4), dpi=180)
    ax1.plot(coverage, precision, "o-", color="#16a34a", linewidth=2, label="selective")
    ax1.scatter([1.0], [raw_p[-1]], color="#64748b", marker="x", s=60, label="raw proposal")
    offsets = [(-28, -8), (4, -18), (16, -6)]
    for x, y, label, offset in zip(coverage, precision, point_labels, offsets):
        ax1.annotate(label, (x, y), xytext=offset, textcoords="offset points", fontsize=8)
    ax1.set_xlim(0, 1.05); ax1.set_ylim(0.80, 1.01)
    ax1.set_xlabel("Accepted proposals / VLM proposals")
    ax1.set_ylabel("Precision among accepted intervals")
    ax1.set_title("Precision–coverage", fontweight="bold")
    style(ax1); ax1.legend(frameon=False, fontsize=8, loc="lower left")
    ax2.bar(np.arange(3), np.array(complete) * 100, color="#f59e0b")
    ax2.set_ylim(0, 100); ax2.set_xticks(np.arange(3), names)
    ax2.set_ylabel("Complete documents auto-accepted (%)")
    ax2.set_title("Complete-record utility", fontweight="bold")
    style(ax2)
    for i, v in enumerate(complete): ax2.text(i, v * 100 + 3, f"{int(v*100)}%", ha="center", fontsize=9)
    stages = ["VLM interval\nproposals", "both endpoints\nanchored", "owned + accepted\nintervals", "complete\ndocuments"]
    values = [proposals, both_anchors["numerator"], accepted, rows[keys[-1]]["complete_document_auto_acceptance"]["numerator"]]
    y = np.arange(len(stages))
    ax3.barh(y, values, color=["#2563eb", "#60a5fa", "#16a34a", "#f59e0b"])
    ax3.set_yticks(y, stages); ax3.invert_yaxis(); ax3.set_xlabel("Count (held-out v003)")
    ax3.set_title("Evidence funnel", fontweight="bold")
    style(ax3)
    for yi, v in zip(y, values): ax3.text(v + max(values) * 0.02, yi, str(v), va="center", fontsize=9)
    ax3.text(
        0.0, -0.25,
        "Endpoint-field anchors: top %s/%s; bottom %s/%s; total %s/%s = %.1f%%\n"
        "Both-endpoint anchoring is the interval-level funnel stage."
        % (
            top_anchor["numerator"], top_anchor["denominator"],
            bottom_anchor["numerator"], bottom_anchor["denominator"],
            endpoint_anchor["numerator"], endpoint_anchor["denominator"],
            endpoint_anchor["value"] * 100,
        ),
        transform=ax3.transAxes, va="top", fontsize=7.2, color="#475569",
    )
    fig.suptitle("Selective assurance makes automation utility explicit", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "F3_assurance_frontier.png", bbox_inches="tight")
    plt.close(fig)


def fig4() -> None:
    d = load(SPATIAL)
    fs = d["full_support_comparison"]
    ms = d["matched_subset_comparison"]
    labels = ["raw", "reread", "risk"]
    full = [fs[k]["aggregate"]["relative_absolute_volume_error"] for k in labels]
    matched = [ms[k]["aggregate"]["relative_absolute_volume_error"] for k in labels]
    support = {row["variant"]: row for row in d["spatial_support"] if row["boundary_index"] == 1}
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13.2, 4.6), dpi=180,
                                      gridspec_kw={"width_ratios": [1.25, 0.8, 1]})
    x = np.arange(3); width = 0.36
    ax1.bar(x - width / 2, full, width, color="#64748b", label="full support")
    ax1.bar(x + width / 2, matched, width, color="#2563eb", label="matched 15 documents")
    ax1.set_xticks(x, labels); ax1.set_ylabel("Reference-relative volume discrepancy")
    ax1.set_ylim(0, 0.17); ax1.set_title("The estimand changes the conclusion", fontweight="bold")
    ax1.legend(frameon=False, fontsize=8); style(ax1)
    for i, (a, b) in enumerate(zip(full, matched)):
        ax1.text(i - width / 2, a + 0.006, f"{a:.4f}", ha="center", fontsize=8)
        ax1.text(i + width / 2, b + 0.006, f"{b:.4f}", ha="center", fontsize=8)
    raw_hull = support["raw"]["convex_hull_area_ratio"]
    risk_hull = support["risk"]["convex_hull_area_ratio"]
    ax2.bar([0 - width / 2, 0 + width / 2], [raw_hull, risk_hull], width,
            color=["#64748b", "#dc2626"])
    ax2.set_xticks([0 - width / 2, 0 + width / 2], ["raw", "risk-aware"])
    ax2.set_ylim(0, 1.05); ax2.set_ylabel("Hull area ratio")
    ax2.set_title("Support retained", fontweight="bold"); style(ax2)
    ax2.text(0 - width / 2, raw_hull + 0.04, f"{raw_hull:.3f}", ha="center", fontsize=8)
    ax2.text(0 + width / 2, risk_hull + 0.04, f"{risk_hull:.3f}", ha="center", fontsize=8)
    dist_names = ["Mean NN", "Mean grid"]
    raw_dist = [support["raw"]["nearest_neighbour_distance_m"]["mean"] / 1000,
                support["raw"]["grid_to_nearest_observation_distance_m"]["mean"] / 1000]
    risk_dist = [support["risk"]["nearest_neighbour_distance_m"]["mean"] / 1000,
                 support["risk"]["grid_to_nearest_observation_distance_m"]["mean"] / 1000]
    ax3.bar(np.arange(2) - width / 2, raw_dist, width, color="#64748b", label="raw")
    ax3.bar(np.arange(2) + width / 2, risk_dist, width, color="#dc2626", label="risk-aware")
    ax3.set_xticks(np.arange(2), dist_names); ax3.set_ylabel("Distance (km)")
    ax3.set_title("Support spacing", fontweight="bold")
    ax3.legend(frameon=False, fontsize=8); style(ax3)
    fig.suptitle("Downstream consequence: acceptance is also a spatial sampling decision", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "F4_spatial_support_consequence.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig1(); fig2(); fig3(); fig4()
    manifest = {
        "manuscript": "paper4",
        "status": "integrated_cg_main_figure_set",
        "figures": [
            {"id": "F1", "file": "figures/F1_trustworthy_framework.png", "purpose": "provenance-grounded assurance framework"},
            {"id": "F2", "file": "figures/F2_vlm_source_shift.png", "purpose": "California VLM/OCR comparison and source shift"},
            {"id": "F3", "file": "figures/F3_assurance_frontier.png", "purpose": "precision, coverage, and complete-document automation"},
            {"id": "F4", "file": "figures/F4_spatial_support_consequence.png", "purpose": "full-support versus matched-support downstream consequence"},
        ],
        "supplementary_figures": [
            {"id": "S1", "file": "figures/F4_risk_coverage_frontier.png", "purpose": "legacy sequence risk frontier"},
            {"id": "S2", "file": "figures/F5_threshold_development_curve.png", "purpose": "development-only threshold curve"},
            {"id": "S3", "file": "figures/F7_controlled_error_mechanisms.png", "purpose": "controlled synthetic perturbation mechanisms"},
        ],
        "source_manifests": {
            str(p.relative_to(ROOT)): digest(p)
            for p in [
                MODERN,
                ASSURANCE,
                ROOT / "results/2026-08-17/P2_VLM_PROPOSAL_ASSURANCE_CALIFORNIA_V003_HELDOUT_002/metrics.json",
                SPATIAL,
            ]
        },
    }
    # This manifest is committed and hash-audited, so bypass platform newline
    # conversion and always emit UTF-8 with LF line endings.
    (Path(__file__).resolve().parent / "figure_manifest.json").write_bytes(
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


if __name__ == "__main__":
    main()
