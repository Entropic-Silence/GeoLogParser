#!/usr/bin/env python3
"""Regenerate manuscript-facing tables, optional figures, and numeric claim audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geologparser.paper_artifacts import paper1_table, paper2_table, paper3_table
from geologparser.major_revision_tables import (
    paper1_major_revision_table,
    paper2_major_revision_tables,
    paper3_major_revision_tables,
)
from geologparser.paper_figures import (
    save_california_cohort_forest,
    save_california_selection_flow,
    save_paper2_sequence_risk,
    save_paper2_threshold_curve,
    save_paper3_spatial_support,
)

from geologparser.manuscript_metrics import audit


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text_lf(path: Path, contents: str) -> None:
    path.write_bytes(contents.encode("utf-8"))


def update_figure_manifest(sources: dict[str, Path], outputs: list[Path]) -> None:
    destination = ROOT / "papers/figure_manifest.json"
    manifest = json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else {
        "scope": "auto-generated traceable figures; individual captions retain audit/protocol/design limits",
        "source_manifests": {},
        "outputs": [],
    }
    indexed = {row["path"]: row for row in manifest.get("outputs", [])}
    for path in outputs:
        relative = path.relative_to(ROOT / "papers").as_posix()
        indexed[relative] = {"path": relative, "sha256": digest(path)}
    for relative, row in list(indexed.items()):
        path = ROOT / "papers" / relative
        if path.is_file():
            row["sha256"] = digest(path)
    manifest["outputs"] = [indexed[key] for key in sorted(indexed)]
    for name, path in sources.items():
        manifest.setdefault("source_manifests", {})[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": digest(path),
        }
    write_text_lf(destination, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(destination)


def load_index(paper: str, publication_core: bool) -> list[dict]:
    path = ROOT / "experiments" / paper / "result_index.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if publication_core:
        rows = [
            {**row, "result_path": str(Path("publication_evidence/result_core") / row["result_path"])}
            for row in rows
        ]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publication-core", action="store_true")
    parser.add_argument(
        "--skip-figures", action="store_true",
        help="regenerate exact text/JSON artifacts without platform-dependent PNG rasterization",
    )
    arguments = parser.parse_args()
    for paper, generator in (("paper1", paper1_table), ("paper2", paper2_table), ("paper3", paper3_table)):
        destination = ROOT / "papers" / paper / "generated/current_results.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_text_lf(destination, generator(load_index(paper, arguments.publication_core), ROOT))
        print(destination)

    california = ROOT / "experiments/paper1/analysis/california_replication_statistics_v001.json"
    california_selection = ROOT / "experiments/paper1/analysis/california_selection_flow_v001.json"
    ablation = ROOT / "experiments/paper2/analysis/california_candidate_pool_ablation_v001.json"
    risk = ROOT / "experiments/paper2/analysis/california_document_risk_v001.json"
    threshold_curve = ROOT / "experiments/paper2/analysis/california_risk_threshold_curve_v001.json"
    spatial = ROOT / "experiments/paper3/analysis/swissgeol_spatial_sensitivity_v001.json"
    major_revision_outputs = {
        ROOT / "papers/paper1/generated/major_revision_tables.md": paper1_major_revision_table(california),
        ROOT / "papers/paper2/generated/major_revision_tables.md": paper2_major_revision_tables(ablation, risk),
        ROOT / "papers/paper3/generated/major_revision_tables.md": paper3_major_revision_tables(spatial),
    }
    for destination, contents in major_revision_outputs.items():
        write_text_lf(destination, contents)
        print(destination)
    if not arguments.skip_figures:
        figure_outputs = [
            ROOT / "papers/paper1/generated/figures/california_cohort_forest.png",
            ROOT / "papers/paper1/generated/figures/california_selection_flow.png",
            ROOT / "papers/paper2/generated/figures/sequence_risk_frontier.png",
            ROOT / "papers/paper2/generated/figures/risk_threshold_curve.png",
            ROOT / "papers/paper3/generated/figures/spatial_support_sensitivity.png",
        ]
        save_california_cohort_forest(california, figure_outputs[0])
        save_california_selection_flow(california_selection, figure_outputs[1])
        save_paper2_sequence_risk(ablation, risk, figure_outputs[2])
        save_paper2_threshold_curve(threshold_curve, figure_outputs[3])
        save_paper3_spatial_support(spatial, figure_outputs[4])
        update_figure_manifest({
            "california_replication": california,
            "california_selection": california_selection,
            "paper2_candidate_pool_ablation": ablation,
            "paper2_document_risk": risk,
            "paper2_threshold_curve": threshold_curve,
            "paper3_spatial_sensitivity": spatial,
        }, figure_outputs)

    report = audit(ROOT / "papers/manuscript_metric_bindings.json", ROOT)
    audit_path = ROOT / "docs/generated/manuscript_metric_audit.json"
    write_text_lf(audit_path, json.dumps(report, indent=2, sort_keys=True) + "\n")
    if not report["passed"]:
        raise SystemExit("\n".join(report["errors"]))
    print(audit_path)


if __name__ == "__main__":
    main()
