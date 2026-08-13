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
        numerator = denominator = None
        if "schema_valid_responses" in metrics:
            numerator, denominator = metrics["schema_valid_responses"], metrics["items"]
        elif "items_with_schema_valid_vlm_record" in metrics:
            numerator, denominator = metrics["items_with_schema_valid_vlm_record"], metrics["items"]
        elif "items_with_any_interval" in metrics:
            numerator, denominator = metrics["items_with_any_interval"], metrics["items"]
        elif "documents_with_borehole_id" in metrics:
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
    axis.set_title("Licensed structured-source protocol only\n(not AI, GT, QC, or a geological model)")
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
