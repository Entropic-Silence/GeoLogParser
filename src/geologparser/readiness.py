"""Evidence-derived publication readiness gates for the three-paper program."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from geologparser.annotation_export import ground_truth_gate


CONTROLLED_FORMAL_ELIGIBILITY = {"formal_silver_benchmark", "formal_synthetic_method", "formal_synthetic_downstream"}
REAL_FORMAL_ELIGIBILITY = {"formal_benchmark", "formal_authoritative_metadata", "formal_method", "formal_downstream"}
FORMAL_ELIGIBILITY = CONTROLLED_FORMAL_ELIGIBILITY | REAL_FORMAL_ELIGIBILITY


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotation_readiness(annotation_root: Path) -> dict[str, Any]:
    paths = sorted(Path(annotation_root).glob("*.json"))
    statuses: Counter[str] = Counter()
    gate_counts: Counter[str] = Counter()
    exportable = 0
    for path in paths:
        annotation = json.loads(path.read_text(encoding="utf-8"))
        statuses[str(annotation.get("annotation_status", "missing"))] += 1
        failures = ground_truth_gate(annotation)
        if not failures:
            exportable += 1
        for failure in failures:
            gate_counts[failure.split(":", 1)[0]] += 1
    return {
        "annotation_root": str(Path(annotation_root).resolve()),
        "annotation_count": len(paths),
        "status_counts": dict(sorted(statuses.items())),
        "ground_truth_exportable_count": exportable,
        "ground_truth_gate_failure_counts": dict(sorted(gate_counts.items())),
    }


def result_index_readiness(index_path: Path) -> dict[str, Any]:
    path = Path(index_path)
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if path.is_file() else []
    eligibility = Counter(str(row.get("paper_eligibility", "missing")) for row in rows)
    return {
        "index_path": str(path.resolve()),
        "index_sha256": _sha256(path) if path.is_file() else None,
        "indexed_experiment_count": len(rows),
        "eligibility_counts": dict(sorted(eligibility.items())),
        "formal_experiment_count": sum(
            count for name, count in eligibility.items() if name in FORMAL_ELIGIBILITY
        ),
        "real_formal_experiment_count": sum(
            count for name, count in eligibility.items() if name in REAL_FORMAL_ELIGIBILITY
        ),
        "controlled_formal_experiment_count": sum(
            count for name, count in eligibility.items() if name in CONTROLLED_FORMAL_ELIGIBILITY
        ),
    }


def project_readiness(
    annotation_roots: Sequence[Path], paper_indexes: Mapping[str, Path],
) -> dict[str, Any]:
    annotations = [annotation_readiness(path) for path in annotation_roots]
    indexes = {paper: result_index_readiness(path) for paper, path in paper_indexes.items()}
    gt_count = sum(value["ground_truth_exportable_count"] for value in annotations)
    paper1_formal = indexes.get("paper1", {}).get("real_formal_experiment_count", 0)
    paper2_formal = indexes.get("paper2", {}).get("real_formal_experiment_count", 0)
    paper3_formal = indexes.get("paper3", {}).get("real_formal_experiment_count", 0)
    gates = {
        "human_ground_truth_exists": gt_count > 0,
        "paper1_formal_results_exist": paper1_formal > 0,
        "paper2_formal_results_exist": paper2_formal > 0,
        "paper3_formal_results_exist": paper3_formal > 0,
    }
    return {
        "readiness_schema_version": "publication_readiness_v001",
        "scope": "evidence-derived status; not a scientific result",
        "annotations": annotations,
        "ground_truth_exportable_count": gt_count,
        "machine_silver_formal_count": sum(
            value.get("eligibility_counts", {}).get("formal_silver_benchmark", 0)
            for value in indexes.values()
        ),
        "paper_indexes": indexes,
        "gates": gates,
        "all_three_papers_empirically_complete": all(gates.values()),
        "interpretation": (
            "Human-GT gates remain separate from the explicitly named machine-Silver "
            "agreement track. Silver runs do not satisfy human-GT publication claims; "
            "audit-only, failure-analysis, and protocol-only runs cannot satisfy formal completion."
        ),
    }


def readiness_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "<!-- AUTO-GENERATED. DO NOT EDIT. -->",
        "# Publication readiness audit",
        "",
        f"Ground-Truth-exportable annotations: **{report['ground_truth_exportable_count']}**.",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name, passed in report["gates"].items():
        lines.append(f"| `{name}` | {'PASSED' if passed else 'NOT COMPLETED'} |")
    lines.extend(["", "| Paper | Indexed runs | Controlled formal | Real formal |", "|---|---:|---:|---:|"])
    for paper, value in sorted(report["paper_indexes"].items()):
        lines.append(
            f"| {paper} | {value['indexed_experiment_count']} | {value['controlled_formal_experiment_count']} | {value['real_formal_experiment_count']} |"
        )
    lines.extend([
        "",
        "Audit/failure-analysis/protocol-only runs are intentionally excluded from formal counts.",
        "False gates require `TBD`/`NOT COMPLETED`; this file is status evidence, not a paper result.",
        "",
    ])
    return "\n".join(lines)
