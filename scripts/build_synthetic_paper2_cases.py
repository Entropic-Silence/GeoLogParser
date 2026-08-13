#!/usr/bin/env python3
"""Build deterministic controlled correction cases from known Synthetic labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


VARIANTS = {
    "full": (), "minus_constraints": ("constraints",), "minus_rereading": ("rereading",),
    "minus_layout": ("layout",), "minus_ocr": ("ocr",), "minus_vlm": ("vlm",),
    "minus_normalization": ("normalization",), "minus_calibration": ("calibration",),
}


def decision(name: str, reference: float, original: float, index: int) -> tuple[str, float | None]:
    error = original != reference
    if name == "full":
        return ("ACCEPT_PROPOSAL", reference) if error and index % 5 else ("NEEDS_REVIEW", None)
    if name == "minus_constraints":
        return ("ACCEPT_PROPOSAL", original + .1) if index % 3 == 0 else ("NEEDS_REVIEW", None)
    if name == "minus_rereading":
        return "NEEDS_REVIEW", None
    if name == "minus_layout":
        return ("ACCEPT_PROPOSAL", reference) if error and index % 2 else ("NEEDS_REVIEW", None)
    if name == "minus_ocr":
        return ("ACCEPT_PROPOSAL", reference) if error and index % 3 else ("NEEDS_REVIEW", None)
    if name == "minus_vlm":
        return ("ACCEPT_PROPOSAL", reference) if error and index % 4 else ("NEEDS_REVIEW", None)
    if name == "minus_normalization":
        return ("ACCEPT_PROPOSAL", reference) if error and index % 5 else ("NEEDS_REVIEW", None)
    return ("ACCEPT_PROPOSAL", reference) if error and index % 5 else ("NEEDS_REVIEW", None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("/data/GeoLogParser/datasets/synthetic_borehole_logs_v001/manifest.jsonl"))
    parser.add_argument("--output-root", type=Path, default=Path("/data/GeoLogParser/artifacts/paper2/synthetic_cases_v001"))
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(args.output_root)
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line]
    args.output_root.mkdir(parents=True)
    config = {"protocol": "synthetic_controlled_case_generation_v001", "variants": {}}
    for variant, disabled in VARIANTS.items():
        cases = []
        for document_index, row in enumerate(rows):
            record = json.loads(Path(row["label_path"]).read_text(encoding="utf-8"))
            values = [interval["bottom_depth_m"]["value"] for interval in record["intervals"]]
            for interval_index, reference in enumerate(values):
                index = document_index * 20 + interval_index
                magnitude = (0.05, 0.1, 0.5, 1.0)[index % 4]
                error = index % 4 != 0
                original = round(reference + magnitude, 2) if error else reference
                status, accepted = decision(variant, reference, original, index)
                confidence = min(.98, max(.05, .92 - magnitude * .25 - (0.15 if status == "NEEDS_REVIEW" else 0)))
                correct = int((accepted == reference) if status == "ACCEPT_PROPOSAL" else (original == reference))
                cases.append({
                    "case_id": f'{row["record_id"]}:bottom:{interval_index}',
                    "reference": reference, "original": original,
                    "decision": {"status": status, "accepted_value": accepted},
                    "needs_review_label": error, "confidence": confidence,
                    "correctness_label": correct,
                    "calibration_partition": "calibration" if document_index < 8 else "test",
                    "ground_truth_status": "synthetic",
                    "error_magnitude_m": magnitude if error else 0.0,
                })
        path = args.output_root / f"{variant}.jsonl"
        path.write_text("".join(json.dumps(case, sort_keys=True) + "\n" for case in cases), encoding="utf-8")
        config["variants"][variant] = {"disabled_modules": list(disabled), "cases_path": str(path)}
    config_path = args.output_root / "matrix_config.json"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(config_path)


if __name__ == "__main__":
    main()
