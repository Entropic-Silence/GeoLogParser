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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
            (repository_root / entry["result_path"] / "metrics.json").read_text()
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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
        if metrics.get("scope") == "authoritative controlled multi-error downstream propagation evaluation":
            candidates.append((entry, metrics))
    if not candidates:
        raise ValueError("no authoritative controlled error-class result is indexed")
    entry, metrics = candidates[-1]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for condition in metrics["conditions"]:
        grouped.setdefault(condition["error_type"], []).append(condition)
    labels = list(grouped)
    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#af7aa1"]
    plt = _plt()
    fig, axes = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    for label, color in zip(labels, colors):
        rows = sorted(grouped[label], key=lambda row: row["severity_index"])
        axes[0].plot(
            [row["severity_index"] for row in rows],
            [row["surface_error"]["mae_m"]["mean"] for row in rows],
            marker="o", label=label.replace("_", " "), color=color,
        )
        axes[1].plot(
            [row["severity_index"] for row in rows],
            [1 - row["spatial_support_coverage"]["mean"] for row in rows],
            marker="o", linestyle="--", color=color,
        )
        axes[1].plot(
            [row["severity_index"] for row in rows],
            [row["topological_mismatch_document_rate"]["mean"] for row in rows],
            marker="s", linestyle="-", color=color,
        )
    axes[0].set_ylabel("Surface MAE (m)")
    axes[0].set_title("Controlled error-class propagation on authoritative records")
    axes[0].grid(alpha=.2)
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].set_xlabel("Within-class severity level (class-specific parameter)")
    axes[1].set_ylabel("Rate")
    axes[1].set_xticks([1, 2, 3])
    axes[1].set_ylim(-.02, .6)
    axes[1].grid(alpha=.2)
    axes[1].text(.01, .95, "solid squares: topology mismatch; dashed circles: support loss", transform=axes[1].transAxes, va="top", fontsize=8)
    axes[1].text(.99, .04, entry["experiment_id"], transform=axes[1].transAxes, ha="right", fontsize=7)
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def save_page_spatial_surface(
    entries: Sequence[Mapping[str, Any]], repository_root: Path, destination: Path,
) -> None:
    """Plot the partial page-coordinate downstream comparison."""
    candidates = []
    for entry in entries:
        metrics = json.loads((repository_root / entry["result_path"] / "metrics.json").read_text())
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
    fig, axis = plt.subplots(figsize=(12, 4))
    axis.axis("off")
    boxes = [
        ("OCR + layout\n+ VLM", .03), ("Initial\nrecord", .21),
        ("C1–C10\nconstraints", .39), ("ROI reread\n+ candidates", .57),
        ("Ranking +\ncalibration", .75), ("Accept or\nreview", .91),
    ]
    for index, (label, x) in enumerate(boxes):
        axis.text(x, .55, label, ha="center", va="center", transform=axis.transAxes,
                  bbox={"boxstyle": "round,pad=.5", "facecolor": "#e7f0f5", "edgecolor": "#285f78"})
        if index < len(boxes) - 1:
            axis.annotate("", xy=(boxes[index + 1][1] - .07, .55), xytext=(x + .07, .55),
                          xycoords=axis.transAxes, textcoords=axis.transAxes,
                          arrowprops={"arrowstyle": "->", "color": "#333"})
    axis.text(.5, .12, "Constraints diagnose and trigger evidence re-reading; they never overwrite values without evidence.",
              transform=axis.transAxes, ha="center", fontsize=10)
    axis.set_title("GeoLogParser proposed method schematic (design, not an empirical result)")
    fig.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)
