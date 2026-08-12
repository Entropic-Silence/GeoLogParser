"""Run and persist the synthetic CPU pipeline smoke test."""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

from geologparser.constraints import default_engine
from geologparser.experiment import create_run_directory
from geologparser.pipeline import run_minimal_baseline


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
    ).stdout.strip() or "UNCOMMITTED"
    version = subprocess.run(["tesseract", "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
    metadata = {
        "experiment_id": "P0_SYNTHETIC_OCR_SMOKE_002",
        "git_commit": git_commit,
        "date": date.today().isoformat(),
        "dataset_version": "synthetic_postscript_fixture_v001",
        "split_version": "not_applicable",
        "model": "tesseract_eng_cpu_smoke",
        "model_revision": version,
        "prompt_version": "not_applicable",
        "seed": None,
        "hardware": {"device": "cpu", "gpu_used": False},
        "software": {"pipeline": "geologparser_0.0.1", "tesseract": version},
        "config": {"ocr_language": "eng", "psm": 6, "constraint_tolerance_m": "0.05"},
    }
    destination = create_run_directory(ROOT / "results", metadata)
    fixture_ps = destination / "synthetic_fixture.ps"
    fixture_png = destination / "synthetic_fixture.png"
    fixture_ps.write_text(
        "%!PS-Adobe-3.0\n<< /PageSize [595 842] >> setpagedevice\n"
        "/Courier findfont 26 scalefont setfont\n"
        "72 730 moveto (Borehole ID: ZK-01) show\n"
        "72 680 moveto (Final Depth: 4.50 m) show\n"
        "72 630 moveto (0.00 1.20 1.20 FILL loose) show\n"
        "72 580 moveto (1.20 4.50 3.30 SILTY_CLAY plastic) show\nshowpage\n",
        encoding="ascii",
    )
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pnggray", "-r300", f"-sOutputFile={fixture_png}", str(fixture_ps)],
        check=True,
    )
    regions, record = run_minimal_baseline(fixture_png, ocr_language="eng")
    constraints = default_engine("0.05").evaluate(record)
    prediction = {"record": record, "text_regions": [region.__dict__ for region in regions]}
    (destination / "predictions.jsonl").write_text(json.dumps(prediction, ensure_ascii=False, default=list) + "\n", encoding="utf-8")
    (destination / "metrics.json").write_text(json.dumps({
        "benchmark_metrics": "TBD",
        "pipeline_completed": True,
        "intervals_emitted": len(record["intervals"]),
        "constraints": [
            {"name": result.name, "passed": result.passed, "score": result.score, "evaluated_count": result.evaluated_count}
            for result in constraints
        ],
    }, indent=2) + "\n", encoding="utf-8")
    observed_id = record["borehole"]["borehole_id"]["value"]
    (destination / "errors.jsonl").write_text(json.dumps({
        "error_type": "OCR_character_error",
        "field": "borehole.borehole_id",
        "expected_fixture_text": "ZK-01",
        "observed": observed_id,
        "note": "synthetic smoke observation; not benchmark evidence",
    }) + "\n", encoding="utf-8")
    (destination / "run.log").write_text(
        f"pipeline_completed=true\nobserved_borehole_id={observed_id}\nintervals={len(record['intervals'])}\n",
        encoding="utf-8",
    )
    fixture_ps.unlink()
    fixture_png.unlink()
    print(destination)


if __name__ == "__main__":
    import shutil
    if shutil.which("tesseract") is None or shutil.which("gs") is None:
        raise SystemExit("Tesseract and Ghostscript are required")
    main()
