"""Paper figures derived only from immutable outputs or explicit schematics."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("paper figures require matplotlib") from exc
    return plt


def save_audit_coverage(entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path) -> None:
    labels, ratios, counts = [], [], []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("ground_truth_tier") == "SYNTHETIC":
            continue
        numerator = denominator = None
        if "schema_valid_responses" in metrics:
            numerator, denominator = metrics["schema_valid_responses"], metrics["items"]
        elif "items_with_schema_valid_vlm_record" in metrics:
            numerator, denominator = metrics["items_with_schema_valid_vlm_record"], metrics["items"]
        elif "items_with_any_interval" in metrics and "items" in metrics:
            numerator, denominator = metrics["items_with_any_interval"], metrics["items"]
        elif "documents_with_borehole_id" in metrics and "documents" in metrics:
            numerator, denominator = metrics["documents_with_borehole_id"], metrics["documents"]
        elif "borehole_id_exact_match" in metrics:
            value = metrics["borehole_id_exact_match"]
            numerator, denominator = value["numerator"], value["denominator"]
        if denominator:
            labels.append(entry["experiment_id"])
            ratios.append(numerator / denominator)
            counts.append(f"{numerator}/{denominator}")
    plt = _plt()
    fig, axis = plt.subplots(figsize=(11, max(4, .35 * len(labels))))
    y = list(range(len(labels)))
    axis.barh(y, ratios, color="#2f6f8f")
    axis.set_yticks(y, labels, fontsize=7)
    axis.invert_yaxis()
    axis.set_xlim(0, 1.05)
    axis.set_xlabel("Engineering-audit availability / parse coverage")
    axis.set_title("Paper I engineering audits (not Ground-Truth accuracy)")
    for index, (value, count) in enumerate(zip(ratios, counts)):
        axis.text(min(1.01, value + .01), index, count, va="center", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_degradation_profiles(manifest: Path, destination: Path) -> None:
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    counts = Counter(row["profile"] for row in rows)
    plt = _plt()
    fig, axis = plt.subplots(figsize=(11, 5))
    labels = sorted(counts)
    axis.bar(range(len(labels)), [counts[label] for label in labels], color="#b76e3b")
    axis.set_xticks(range(len(labels)), labels, rotation=55, ha="right", fontsize=8)
    axis.set_ylabel("Derived images")
    axis.set_title("Parameterized robustness inputs (no accuracy without GT)")
    axis.text(.99, .97, f"n={len(rows)} derivatives", transform=axis.transAxes, ha="right", va="top")
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_authoritative_interval_pilot(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot the narrow source-agreement interval result from immutable metrics."""

    candidates = []
    for entry in entries:
        metrics = json.loads(
            (repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8")
        )
        if metrics.get("scope") == "authoritative-interval benchmark evaluation":
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no authoritative interval benchmark result is indexed")
    # Keep the main benchmark figure tied to the largest held-out reference
    # rather than replacing it when a small cross-source diagnostic is added.
    entry, metrics = max(candidates, key=lambda item: int(item[1].get("document_count", 0)))
    interval = metrics["interval_metrics"]
    labels = ["Precision", "Recall", "F1", "Full-document\nexact"]
    values = [
        interval["interval_precision"]["value"],
        interval["interval_recall"]["value"],
        interval["interval_f1"]["value"],
        metrics["document_full_exact"]["value"],
    ]
    plt = _plt()
    fig, axis = plt.subplots(figsize=(7.5, 4.8))
    bars = axis.bar(labels, values, color=["#2f6f8f", "#b76e3b", "#4c956c", "#7b6d8d"])
    axis.set_ylim(0, 1.08)
    axis.set_ylabel("Score")
    axis.set_title("Held-out source-agreement interval benchmark")
    axis.grid(axis="y", alpha=.2)
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, value + .02, f"{value:.3f}", ha="center")
    axis.text(
        .01, -.23,
        (
            f'{metrics["document_count"]} selected documents; '
            f'{metrics["reference_interval_count"]} reference / '
            f'{metrics["predicted_interval_count"]} predicted intervals; '
            "explicit-table source-agreement subset, not a representative sample"
        ),
        transform=axis.transAxes, fontsize=8,
    )
    axis.text(.99, .03, entry["experiment_id"], transform=axis.transAxes, ha="right", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_source_disjoint_transfer(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Contrast selected same-source held-out results with external transfer agreement."""
    values: dict[tuple[str, str], tuple[float, float]] = {}
    for entry in entries:
        metrics = json.loads(
            (repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8")
        )
        model = json.loads(
            (repository_root / entry["result_path"] / "run.json").read_text(encoding="utf-8")
        )["model"].lower()
        backend = "Tesseract" if "tesseract" in model else "RapidOCR" if "rapidocr" in model else None
        if backend is None:
            continue
        if "TG_CONTENT_HELDOUT" in entry["experiment_id"]:
            panel = "Selected Thurgau\nsource-agreement"
        elif metrics.get("scope") == "source-disjoint authoritative-database interval transfer evaluation":
            panel = "External source-disjoint\ndatabase transfer"
        else:
            continue
        values[(panel, backend)] = (
            float(metrics["interval_metrics"]["interval_f1"]["value"] or 0.0),
            metrics["documents_with_predictions"] / metrics["document_count"],
        )
    panels = ["Selected Thurgau\nsource-agreement", "External source-disjoint\ndatabase transfer"]
    backends = ["Tesseract", "RapidOCR"]
    missing = [(panel, backend) for panel in panels for backend in backends if (panel, backend) not in values]
    if missing:
        raise ValueError(f"missing source-disjoint figure inputs: {missing}")
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    colors = {"Tesseract": "#2f6f8f", "RapidOCR": "#b76e3b"}
    width = 0.34
    x = list(range(len(panels)))
    for offset, backend in zip((-width / 2, width / 2), backends):
        f1 = [values[(panel, backend)][0] for panel in panels]
        coverage = [values[(panel, backend)][1] for panel in panels]
        bars_f1 = axes[0].bar([item + offset for item in x], f1, width, label=backend, color=colors[backend])
        bars_cov = axes[1].bar([item + offset for item in x], coverage, width, label=backend, color=colors[backend])
        for axis, bars, numbers in ((axes[0], bars_f1, f1), (axes[1], bars_cov, coverage)):
            for bar, number_value in zip(bars, numbers):
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    min(1.02, number_value + .025),
                    f"{number_value:.3f}", ha="center", fontsize=8,
                )
    axes[0].set_title("Interval F1 / transfer agreement F1")
    axes[1].set_title("Records with any interval output")
    for axis in axes:
        axis.set_xticks(x, panels)
        axis.set_ylim(0, 1.08)
        axis.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Ratio")
    axes[1].legend(loc="upper right")
    fig.suptitle("Frozen-parser performance under source shift")
    fig.text(
        .5, .01,
        "External values are agreement with same-object official database sequences; complete page/database agreement is unverified.",
        ha="center", fontsize=8,
    )
    fig.tight_layout(rect=(0, .05, 1, .94))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_california_replication(analysis_path: Path, destination: Path) -> None:
    """Plot paired document-bootstrap F1 differences across California freezes."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    panels = [
        ("OCR: RapidOCR − Tesseract", "ocr_paired_bootstrap", "#2f6f8f"),
        ("Constraint sequence − raw", "constraint_paired_bootstrap", "#b76e3b"),
    ]
    labels = ["v001 held-out", "v002 external", "v003 prospective", "Combined\ndescriptive"]
    sources = [
        analysis["freezes"]["v001"],
        analysis["freezes"]["v002_external"],
        analysis["freezes"]["v003_prospective"],
        analysis["combined_descriptive"],
    ]
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
    for axis, (title, key, color) in zip(axes, panels):
        values = [source[key]["delta_left_minus_right"]["f1"] for source in sources]
        estimates = [value["observed"] for value in values]
        lower = [estimate - value["bootstrap_percentile_95_ci"][0] for estimate, value in zip(estimates, values)]
        upper = [value["bootstrap_percentile_95_ci"][1] - estimate for estimate, value in zip(estimates, values)]
        x = list(range(len(labels)))
        axis.errorbar(x, estimates, yerr=[lower, upper], fmt="o", capsize=5, color=color)
        axis.axhline(0, color="#555555", linewidth=1, linestyle="--")
        axis.set_xticks(x, labels)
        axis.set_title(title)
        axis.grid(axis="y", alpha=.2)
        for position, estimate in zip(x, estimates):
            axis.text(position, estimate + .012, f"{estimate:.3f}", ha="center", fontsize=8)
    axes[0].set_ylabel("Paired pooled-F1 difference")
    fig.suptitle("California cross-freeze replication (20,000 document-cluster bootstrap samples)")
    fig.text(
        .5,
        .01,
        "Bars are percentile 95% intervals; combined estimates are descriptive because sampling probabilities are unknown.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, .05, 1, .93))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_california_cohort_forest(analysis_path: Path, destination: Path) -> None:
    """Plot per-cohort RapidOCR F1 with document-cluster bootstrap intervals."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    order = [
        ("v001", "v001"),
        ("v002", "v002_external"),
        ("v003", "v003_prospective"),
        ("v004", "v004_prospective"),
        ("v005", "v005_external"),
        ("Pooled*", None),
    ]
    rows = []
    for label, key in order:
        source = analysis["combined_descriptive"] if key is None else analysis["freezes"][key]
        metric = source["rapidocr_document_cluster_metrics"]
        rows.append((label, metric["f1"], metric["bootstrap_percentile_95_ci"]["f1"]))
    plt = _plt()
    fig, axis = plt.subplots(figsize=(8.5, 5.4))
    y = list(reversed(range(len(rows))))
    values = [row[1] for row in rows]
    lower = [value - row[2][0] for value, row in zip(values, rows)]
    upper = [row[2][1] - value for value, row in zip(values, rows)]
    colors = ["#2f6f8f"] * 5 + ["#777777"]
    for index, (position, value, low, high, color) in enumerate(zip(y, values, lower, upper, colors)):
        marker = "s" if index == len(rows) - 1 else "o"
        axis.errorbar(value, position, xerr=[[low], [high]], fmt=marker, capsize=4, color=color)
        axis.text(value + high + .008, position, f"{value:.3f}", va="center", fontsize=8)
    axis.set_yticks(y, [row[0] for row in rows])
    axis.set_xlim(0.2, 0.61)
    axis.set_xlabel("Interval F1 (document-cluster percentile 95% interval)")
    axis.set_title("California multi-cohort extraction stability")
    axis.grid(axis="x", alpha=.2)
    axis.axhline(.5, color="#bbbbbb", linewidth=.8)
    fig.text(
        .5, .025,
        "*Pooled estimate is descriptive; cohorts have no population sampling weights.",
        ha="center", fontsize=8,
    )
    fig.tight_layout(rect=(0, .07, 1, 1))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_california_selection_flow(analysis_path: Path, destination: Path) -> None:
    """Render the deterministic California eligibility and acquisition flow."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    stages = analysis["stages"]
    plt = _plt()
    fig, axis = plt.subplots(figsize=(10.5, 7.2))
    axis.axis("off")
    y_positions = [0.88 - index * (0.72 / max(1, len(stages) - 1)) for index in range(len(stages))]
    for index, (stage, y) in enumerate(zip(stages, y_positions)):
        label = f"{stage['label']}\n{stage['document_count']:,} documents / {stage['interval_count']:,} intervals"
        axis.text(0.58, y, label, ha="center", va="center", fontsize=9, bbox={"boxstyle": "round,pad=0.5", "facecolor": "#eef4f7", "edgecolor": "#2f6f8f"})
        if index:
            previous_y = y_positions[index - 1]
            removed = stage.get("documents_removed_from_previous", 0)
            annotation = f"-{removed:,} documents" if removed >= 0 else "fixed acquisition budget"
            axis.annotate(
                "", xy=(0.58, y + .048), xytext=(0.58, previous_y - .048),
                arrowprops={"arrowstyle": "->", "color": "#555555"},
            )
            axis.text(0.20, (previous_y + y) / 2, annotation, ha="left", va="center", fontsize=8, color="#444444")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_title("California eligibility, acquisition, and formal-evaluation flow", fontsize=12)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_paper2_sequence_risk(
    ablation_path: Path, risk_path: Path, destination: Path,
) -> None:
    """Plot the recovery/harm frontier on California v004/v005."""
    ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
    risk = json.loads(risk_path.read_text(encoding="utf-8"))
    labels = {
        "candidate_pool_without_sequence": "All candidates",
        "monotonic_sequence": "Monotonic",
        "continuity_sequence": "+ continuity",
        "complete_sequence": "Complete",
    }
    offsets = {
        "v004": {
            "candidate_pool_without_sequence": (6, -12),
            "monotonic_sequence": (6, 5),
            "continuity_sequence": (6, -14),
            "complete_sequence": (6, 6),
        },
        "v005": {
            "candidate_pool_without_sequence": (6, -12),
            "monotonic_sequence": (6, 5),
            "continuity_sequence": (6, -15),
            "complete_sequence": (6, 7),
        },
    }
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for axis, freeze in zip(axes, ("v004", "v005")):
        data = ablation["freezes"][freeze]
        for variant, label in labels.items():
            f1 = data["metrics"][variant]["interval_f1"]["value"]
            fcr = data["correction_safety"][variant]["false_correction_rate"]
            axis.scatter(fcr, f1, s=55)
            axis.annotate(label, (fcr, f1), xytext=offsets[freeze][variant], textcoords="offset points", fontsize=8)
        risk_f1 = risk["freezes"][freeze]["addition_only_risk"]["f1"]
        axis.scatter(0, risk_f1, marker="*", s=130, color="#2ca02c", label="Addition-only")
        axis.annotate("Addition-only", (0, risk_f1), xytext=(8, -3), textcoords="offset points", fontsize=8, color="#206d20")
        axis.set_title(freeze)
        axis.set_xlabel("False-correction rate")
        axis.grid(alpha=.2)
        axis.set_xlim(-.025, .38)
        axis.set_ylim(.39, .60)
    axes[0].set_ylabel("Interval F1")
    axes[0].legend(loc="lower right", fontsize=8)
    fig.suptitle("Sequence recovery versus correction harm (fixed candidate pool)")
    fig.tight_layout(rect=(0, 0, 1, .94))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_paper2_threshold_curve(analysis_path: Path, destination: Path) -> None:
    """Plot development-only risk/coverage/utility versus the node threshold."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    rows = [row for row in analysis["curve"] if row["threshold"] >= 2.9]
    thresholds = [row["threshold"] for row in rows]
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    axes[0].plot(thresholds, [row["coverage_all_documents"] for row in rows], label="Document coverage")
    axes[0].plot(thresholds, [row["interval_f1"] for row in rows], label="Interval F1")
    axes[0].set_ylabel("Ratio")
    axes[0].legend()
    axes[1].plot(thresholds, [0.0 if row["action_fcr"] is None else row["action_fcr"] for row in rows], label="Action FCR")
    axes[1].plot(thresholds, [row["worsened_documents"] / analysis["document_count"] for row in rows], label="Worsened-document rate")
    axes[1].set_ylabel("Observed development risk")
    axes[1].legend()
    for axis in axes:
        axis.axvline(analysis["chosen_threshold"], color="#b76e3b", linestyle="--", linewidth=1)
        axis.set_xlabel("Raw node-score threshold")
        axis.grid(alpha=.2)
    fig.suptitle("Addition-only threshold selection on v001/v002 development evidence")
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_paper3_spatial_support(analysis_path: Path, destination: Path) -> None:
    """Plot full-support/matched-subset results and boundary support."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    variants = ["raw", "reread", "risk"]
    labels = ["Raw", "Reread", "Risk-aware"]
    colors = ["#e15759", "#4e79a7", "#59a14f"]
    full = analysis["full_support_comparison"]
    matched = analysis["matched_subset_comparison"]
    support = {
        row["variant"]: row for row in analysis["spatial_support"]
        if row["boundary_index"] == 1
    }
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    x = list(range(3))
    full_values = [full[v]["aggregate"]["relative_absolute_volume_error"] for v in variants]
    jackknife = analysis["volume_jackknife"]["full_support"]["variants"]
    lower = [value - jackknife[variant]["relative_absolute_volume_error"]["minimum"] for variant, value in zip(variants, full_values)]
    upper = [jackknife[variant]["relative_absolute_volume_error"]["maximum"] - value for variant, value in zip(variants, full_values)]
    axes[0].bar(x, full_values, yerr=[lower, upper], capsize=5, color=colors)
    axes[0].set_title("Full-support volume diagnostic\n(error bars: borehole jackknife range)")
    axes[0].set_ylabel("Relative absolute volume error")
    axes[1].bar(x, [matched[v]["aggregate"]["relative_absolute_volume_error"] for v in variants], color=colors)
    axes[1].set_title("Matched 15-document subset")
    axes[2].bar(x, [support[v]["convex_hull_area_ratio"] for v in variants], color=colors)
    axes[2].set_title("Boundary 1 hull-area support")
    axes[2].set_ylabel("Accepted/reference hull area")
    for axis in axes:
        axis.set_xticks(x, labels, rotation=18)
        axis.grid(axis="y", alpha=.2)
    fig.suptitle("Selection changes both error and spatial support")
    fig.tight_layout(rect=(0, 0, 1, .94))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_padova_locations(location_manifest: Path, destination: Path) -> None:
    rows = [json.loads(line) for line in location_manifest.read_text(encoding="utf-8").splitlines() if line]
    groups = {
        "Grizzaga": [row for row in rows if row["link_key"].startswith("GS")],
        "Panaro": [row for row in rows if row["link_key"].startswith("PS")],
        "Tagliamento": [row for row in rows if row["link_key"].startswith(("TS", "TPS"))],
    }
    plt = _plt()
    fig, axis = plt.subplots(figsize=(8, 6))
    colors = {"Grizzaga": "#4c78a8", "Panaro": "#f58518", "Tagliamento": "#54a24b"}
    for name, values in groups.items():
        axis.scatter([row["longitude"] for row in values], [row["latitude"] for row in values], label=name, s=48, color=colors[name])
        for row in values:
            axis.annotate(row["link_key"], (row["longitude"], row["latitude"]), xytext=(3, 3), textcoords="offset points", fontsize=7)
    axis.set_xlabel("Longitude (EPSG:4326)")
    axis.set_ylabel("Latitude (EPSG:4326)")
    axis.set_title("Padova source-provided borehole locations\n(unverified; not interval GT)")
    axis.legend()
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_error_propagation(entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path) -> None:
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        conditions = metrics.get("conditions", [])
        if (
            conditions
            and isinstance(conditions[0].get("mae_m"), Mapping)
            and metrics.get("data_status") != "licensed_source_structured_data_pending_human_spatial_review"
        ):
            candidates.append((entry, conditions))
    if not candidates:
        raise ValueError("no multi-seed error-propagation result is indexed")
    entry, conditions = candidates[-1]
    x = [condition["magnitude_m"] for condition in conditions]
    y = [condition["mae_m"]["mean"] for condition in conditions]
    errors = [condition["mae_m"]["std"] for condition in conditions]
    plt = _plt()
    fig, axis = plt.subplots(figsize=(7, 5))
    axis.errorbar(x, y, yerr=errors, marker="o", capsize=4, color="#8c564b")
    axis.set_xlabel("Injected boundary perturbation magnitude (m)")
    axis.set_ylabel("Synthetic IDW surface MAE (m)")
    axis.set_title("Protocol-only synthetic propagation\n(not real geological sensitivity)")
    axis.grid(alpha=.25)
    axis.text(.02, .96, entry["experiment_id"], transform=axis.transAxes, va="top", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_source_field_propagation(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot only licensed structured-source proxy results, never formal results."""

    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("data_status") != "licensed_source_structured_data_pending_human_spatial_review":
            continue
        conditions = metrics.get("conditions", [])
        if conditions and isinstance(conditions[0].get("mae_m"), Mapping):
            candidates.append((entry, metrics, conditions))
    if not candidates:
        raise ValueError("no licensed structured-source proxy result is indexed")
    entry, metrics, conditions = candidates[-1]
    x = [condition["magnitude_m"] for condition in conditions]
    y = [condition["mae_m"]["mean"] for condition in conditions]
    errors = [condition["mae_m"]["std"] for condition in conditions]
    plt = _plt()
    fig, axis = plt.subplots(figsize=(7, 5))
    axis.errorbar(x, y, yerr=errors, marker="o", capsize=4, color="#3a7d44")
    axis.set_xlabel("Injected source-field perturbation magnitude (m)")
    axis.set_ylabel("IDW proxy-surface MAE (m)")
    axis.set_title("Licensed structured-source protocol only\n(not image-derived extraction, reference, QC, or a geological model)")
    axis.grid(alpha=.25)
    axis.text(
        .02, .96,
        f'{entry["experiment_id"]}\nn={metrics["source_record_count"]} source records',
        transform=axis.transAxes, va="top", fontsize=7,
    )
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_image_boundary_surface(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot the frozen real image-boundary downstream diagnostic."""
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if (
            metrics.get("comparison") == "raw_image_boundary_vs_constraint_reread_boundary_vs_authoritative_reference_surface"
            and "surface" in metrics
        ):
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no image-boundary surface diagnostic is indexed")
    entry, metrics = candidates[-1]
    surface = metrics["surface"]
    values = [
        surface["raw"]["boundary_mae_m"], surface["final"]["boundary_mae_m"],
        surface["raw"]["surface_error"]["mae_m"], surface["final"]["surface_error"]["mae_m"],
    ]
    labels = ["Raw\nboundary", "Reread\nboundary", "Raw\nsurface", "Reread\nsurface"]
    plt = _plt()
    fig, axis = plt.subplots(figsize=(7.5, 4.8))
    bars = axis.bar(labels, values, color=["#9c755f", "#59a14f", "#9c755f", "#59a14f"])
    axis.set_ylabel("MAE (m)")
    axis.set_title("Held-out image-boundary downstream diagnostic")
    axis.grid(axis="y", alpha=.2)
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, value + max(values) * .02, f"{value:.3f}", ha="center", fontsize=8)
    axis.text(.01, -.22, f'{metrics["document_count"]} documents; {metrics["query_count"]} IDW queries; coordinates/elevations from authoritative records', transform=axis.transAxes, fontsize=8)
    axis.text(.99, .97, entry["experiment_id"], transform=axis.transAxes, ha="right", va="top", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_image_multiboundary_surface(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot per-boundary MAE and support for the real multi-boundary diagnostic."""
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("scope") == "real image-derived multi-boundary downstream surface diagnostic":
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no image multi-boundary surface diagnostic is indexed")
    entry, metrics = candidates[-1]
    rows = metrics["per_boundary"]
    indexes = [row["boundary_index"] for row in rows]
    raw = [row["variants"]["raw"]["surface_error"]["mae_m"] for row in rows]
    final = [row["variants"]["final"]["surface_error"]["mae_m"] for row in rows]
    raw_coverage = [row["variants"]["raw"]["coverage"] for row in rows]
    final_coverage = [row["variants"]["final"]["coverage"] for row in rows]
    plt = _plt()
    fig, axes = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    width = .36
    axes[0].bar([x - width / 2 for x in indexes], raw, width=width, color="#9c755f", label="Raw")
    axes[0].bar([x + width / 2 for x in indexes], final, width=width, color="#59a14f", label="Reread")
    axes[0].set_ylabel("Surface MAE (m)")
    axes[0].set_title("Held-out multi-boundary image-to-surface diagnostic")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=.2)
    axes[1].plot(indexes, raw_coverage, marker="o", color="#9c755f", label="Raw")
    axes[1].plot(indexes, final_coverage, marker="o", color="#59a14f", label="Reread")
    axes[1].set_xlabel("Ordered interval boundary index")
    axes[1].set_ylabel("Spatial point coverage")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_xticks(indexes)
    axes[1].grid(alpha=.2)
    axes[1].legend()
    axes[1].text(.99, .04, entry["experiment_id"], transform=axes[1].transAxes, ha="right", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_controlled_error_class_propagation(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot surface impact, support, and topology by controlled error class."""
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("scope") == "authoritative controlled multi-error downstream propagation evaluation":
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no authoritative controlled error-class result is indexed")
    entry, metrics = candidates[-1]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for condition in metrics["conditions"]:
        grouped.setdefault(condition["error_type"], []).append(condition)
    labels = [
        "boundary_shift", "coordinate_shift", "missing_boundary",
        "merged_layer", "split_layer", "duplicate_boundary",
    ]
    titles = {
        "boundary_shift": "Boundary displacement",
        "coordinate_shift": "Coordinate displacement",
        "missing_boundary": "Missing boundary",
        "merged_layer": "Merged layer",
        "split_layer": "Split layer",
        "duplicate_boundary": "Duplicate boundary",
    }
    x_labels = {
        "boundary_shift": "Displacement (m)",
        "coordinate_shift": "Displacement (m)",
        "missing_boundary": "Affected documents",
        "merged_layer": "Affected documents",
        "split_layer": "Affected documents",
        "duplicate_boundary": "Affected documents",
    }
    plt = _plt()
    from matplotlib.lines import Line2D
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for axis, label in zip(axes.flat, labels):
        rows = sorted(grouped[label], key=lambda row: row["severity_index"])
        x = [float(row["parameter"]) for row in rows]
        if rows[0]["parameter_unit"] == "affected_document_fraction":
            x = [value * 100 for value in x]
        axis.plot(
            x,
            [row["surface_error"]["mae_m"]["mean"] for row in rows],
            marker="o", color="#4e79a7", label="Surface MAE",
        )
        rate_axis = axis.twinx()
        rate_axis.plot(
            x,
            [1 - row["spatial_support_coverage"]["mean"] for row in rows],
            marker="o", linestyle="--", color="#e15759", label="Support loss",
        )
        rate_axis.plot(
            x,
            [row["topological_mismatch_document_rate"]["mean"] for row in rows],
            marker="s", linestyle=":", color="#59a14f", label="Topology mismatch",
        )
        axis.set_title(titles[label])
        axis.set_xlabel(x_labels[label] + (" (%)" if rows[0]["parameter_unit"] == "affected_document_fraction" else ""))
        axis.set_ylabel("Surface MAE (m)")
        rate_axis.set_ylabel("Rate")
        rate_axis.set_ylim(-.03, 1.03)
        axis.set_xticks(x)
        axis.grid(alpha=.2)
    handles = [
        Line2D([], [], color="#4e79a7", marker="o", label="Surface MAE"),
        Line2D([], [], color="#e15759", marker="o", linestyle="--", label="Support loss"),
        Line2D([], [], color="#59a14f", marker="s", linestyle=":", label="Topology mismatch"),
    ]
    fig.suptitle("Within-class dose-response on authoritative records; x-axes are not comparable", y=.995)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, .955), ncol=3, frameon=False)
    fig.text(.99, .01, entry["experiment_id"], ha="right", fontsize=7)
    fig.tight_layout(rect=(0, .03, 1, .88))
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_page_spatial_surface(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot the partial page-coordinate downstream comparison."""
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("scope") == "real page-coordinate image-boundary downstream surface diagnostic":
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no page-coordinate downstream result is indexed")
    entry, metrics = candidates[-1]
    order = [
        "page_coordinate_reference_boundary",
        "page_coordinate_raw_boundary",
        "page_coordinate_reread_boundary",
        "authoritative_coordinate_reread_boundary",
    ]
    labels = ["Page coord.\nreference depth", "Page coord.\nraw depth", "Page coord.\nreread depth", "Authoritative coord.\nreread depth"]
    rows = [metrics["variants"][name] for name in order]
    plt = _plt()
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].bar(range(len(rows)), [row["surface_error"]["mae_m"] for row in rows], color=["#e15759", "#f28e2b", "#59a14f", "#4e79a7"])
    axes[0].set_ylabel("Surface MAE (m)")
    axes[0].set_title("Page-coordinate coverage in the downstream surface workflow")
    axes[0].grid(axis="y", alpha=.2)
    axes[1].bar(range(len(rows)), [row["coverage"] for row in rows], color=["#e15759", "#f28e2b", "#59a14f", "#4e79a7"])
    axes[1].set_ylabel("Spatial point coverage")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_xticks(range(len(labels)), labels, fontsize=8)
    axes[1].grid(axis="y", alpha=.2)
    axes[1].text(.01, .95, "Collar elevations are authoritative in every variant", transform=axes[1].transAxes, va="top", fontsize=8)
    axes[1].text(.99, .04, entry["experiment_id"], transform=axes[1].transAxes, ha="right", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_method_schematic(destination: Path) -> None:
    plt = _plt()
    fig, axis = plt.subplots(figsize=(12, 5.2))
    axis.axis("off")
    boxes = {
        "raw": (.08, .68, "First pass R"),
        "candidates": (.08, .34, "Positioned candidates C\n(field + geometry evidence)"),
        "graph": (.36, .51, "Candidate graph\nnode + admissible-edge scores"),
        "sequence": (.62, .51, "Dynamic programming\nsequence S"),
        "unselective": (.88, .70, "Unselective output\nS"),
        "risk": (.88, .31, "Addition-only policy\nR + accepted A / abstain"),
    }
    for _, (x, y, label) in boxes.items():
        axis.text(x, y, label, ha="center", va="center", transform=axis.transAxes,
                  bbox={"boxstyle": "round,pad=.5", "facecolor": "#e7f0f5", "edgecolor": "#285f78"})

    def arrow(source: str, target: str) -> None:
        left = boxes[source]
        right = boxes[target]
        axis.annotate(
            "", xy=(right[0] - .09, right[1]), xytext=(left[0] + .09, left[1]),
            xycoords=axis.transAxes, textcoords=axis.transAxes,
            arrowprops={"arrowstyle": "->", "color": "#333"},
        )

    arrow("raw", "graph")
    arrow("candidates", "graph")
    arrow("graph", "sequence")
    arrow("sequence", "unselective")
    arrow("sequence", "risk")
    axis.text(.5, .10, "Deterministic geometry reconstructs depths; the risk branch preserves R and accepts only non-overlapping high-score additions.",
              transform=axis.transAxes, ha="center", fontsize=9)
    axis.set_title("Risk-aware sequence reconstruction (method schematic, not an empirical result)")
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)
