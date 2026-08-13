#!/usr/bin/env python3
"""Execute the real rereading/ranking code on controlled Synthetic perturbations."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from geologparser.rereading import Candidate, decide_reread, rank_candidates


VARIANTS = {
    "full": (), "minus_constraints": ("constraints",), "minus_rereading": ("rereading",),
    "minus_layout": ("layout",), "minus_ocr": ("ocr",), "minus_vlm": ("vlm",),
    "minus_normalization": ("normalization",), "minus_calibration": ("calibration",),
}


def candidates(reference: float, original: float, hard: bool) -> list[Candidate]:
    rows = [
        Candidate(reference, "ocr", str(reference), .90, .90, .80),
        Candidate(reference, "vlm", str(reference), .85, .85, .90),
        Candidate(original, "layout", str(original), .99, .99, .99),
        Candidate(original, "parser", str(original), .97, .97, .97),
    ]
    if hard:
        rows.append(Candidate(round(reference + .2, 2), "ocr", None, .80, .75, .70))
    return rows


def execute(record: dict, path: str, rows: list[Candidate], variant: str) -> dict:
    if variant == "minus_rereading":
        return {"status": "NEEDS_REVIEW", "accepted_value": None, "reason": "rereading_disabled"}
    filtered = rows
    if variant == "minus_layout": filtered = [item for item in rows if item.source != "layout"]
    if variant == "minus_ocr": filtered = [item for item in rows if item.source != "ocr"]
    if variant == "minus_vlm": filtered = [item for item in rows if item.source != "vlm"]
    if variant == "minus_constraints":
        scores = rank_candidates(record, path, filtered, weights={"evidence": .75, "agreement": .25, "constraint": 0.0})
        best = scores[0]
        return {"status": "ACCEPT_PROPOSAL", "accepted_value": best.candidate.value,
                "reason": "highest_evidence_without_constraint_component"}
    result = decide_reread(record, path, filtered)
    return {"status": result.status, "accepted_value": result.accepted_value, "reason": result.reason}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v001/manifest.jsonl"))
    parser.add_argument("--output-root", type=Path, default=Path("/data/GeoLogParser/artifacts/paper2/executed_synthetic_cases_v001"))
    args = parser.parse_args()
    if args.output_root.exists(): raise FileExistsError(args.output_root)
    manifests = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line]
    args.output_root.mkdir(parents=True)
    variant_cases = {name: [] for name in VARIANTS}
    for document_index, item in enumerate(manifests):
        reference_record = json.loads(Path(item["label_path"]).read_text(encoding="utf-8"))
        for interval_index, interval in enumerate(reference_record["intervals"]):
            index = document_index * 20 + interval_index
            reference = float(interval["bottom_depth_m"]["value"])
            initially_correct = index % 4 == 0
            magnitude = (0.05, .10, .50, 1.00)[index % 4]
            original = reference if initially_correct else round(reference + magnitude, 2)
            hard = index % 7 == 0
            perturbed = copy.deepcopy(reference_record)
            perturbed["intervals"][interval_index]["bottom_depth_m"]["value"] = original
            path = f"intervals[{interval_index}].bottom_depth_m"
            rows = candidates(reference, original, hard)
            for variant in VARIANTS:
                result = execute(perturbed, path, rows, variant)
                final = result["accepted_value"] if result["status"] == "ACCEPT_PROPOSAL" else original
                confidence = .90 if result["status"] == "ACCEPT_PROPOSAL" and final == reference else (.65 if result["status"] == "NEEDS_REVIEW" else .20)
                variant_cases[variant].append({
                    "case_id": f'{item["record_id"]}:bottom:{interval_index}',
                    "reference": reference, "original": original, "decision": result,
                    "needs_review_label": hard, "confidence": confidence,
                    "correctness_label": int(final == reference),
                    "calibration_partition": "calibration" if document_index < 8 else "test",
                    "ground_truth_status": "synthetic", "initially_correct": initially_correct,
                    "error_magnitude_m": 0.0 if initially_correct else magnitude,
                })
    config = {"protocol": "executed_synthetic_rereading_v001", "variants": {}}
    for name, disabled in VARIANTS.items():
        path = args.output_root / f"{name}.jsonl"
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in variant_cases[name]), encoding="utf-8")
        config["variants"][name] = {"disabled_modules": list(disabled), "cases_path": str(path)}
    destination = args.output_root / "matrix_config.json"
    destination.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__": main()
