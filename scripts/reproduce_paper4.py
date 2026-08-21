#!/usr/bin/env python3
"""Rebuild the redistributable Paper 4 review package and run its audits.

This is a result-reproduction workflow: it uses committed analysis JSON,
publication evidence projections, manifests, and scripts. It does not download
model weights, access source PDFs, or rerun a VLM/OCR model.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(label: str, *command: str) -> None:
    print(f"\n[Paper4] {label}: {' '.join(command)}", flush=True)
    subprocess.run([sys.executable, *command], cwd=ROOT, check=True)


def run_external(label: str, *command: str) -> None:
    print(f"\n[Paper4] {label}: {' '.join(command)}", flush=True)
    subprocess.run(list(command), cwd=ROOT, check=True)


def final_manuscript_command() -> list[str]:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        raise RuntimeError(
            "PowerShell is required to build the final C&G manuscript; "
            "install PowerShell 7 or provide powershell.exe on PATH"
        )
    command = [powershell, "-NoProfile"]
    if sys.platform == "win32":
        command.extend(["-ExecutionPolicy", "Bypass"])
    command.extend(
        [
            "-File",
            str(ROOT / "papers" / "paper4" / "submission" / "cageo" / "build.ps1"),
            "-Final",
        ]
    )
    return command


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="also run the repository test suite after rebuilding publication artifacts",
    )
    args = parser.parse_args()

    run("build integrated C&G figures", "papers/paper4/build_cg_figures.py")
    run_external("build final C&G manuscript", *final_manuscript_command())
    run("assemble manuscript-facing upload bundle", "scripts/build_paper4_upload_bundle.py")
    run("rebuild redistributable evidence core", "scripts/build_publication_evidence.py")
    run(
        "rebuild publication-facing tables and metric audit",
        "scripts/regenerate_publication_artifacts.py",
        "--publication-core",
        "--skip-figures",
    )
    run("verify headline claims", "papers/paper4/verify_claims.py")
    run("verify claim-to-evidence map", "papers/paper4/audit_claim_evidence.py")
    run("run C&G submission gate", "scripts/audit_paper4_submission.py")
    run("rebuild manuscript review packages", "scripts/build_paper_packages.py")
    run(
        "verify frozen C&G artifact hashes and release metadata",
        "scripts/build_cageo_artifact_manifest.py",
        "--verify-only",
    )
    run("verify generated UTF-8/LF artifacts", "scripts/audit_generated_text_format.py")
    if args.with_tests:
        run("run full test suite", "-m", "pytest", "-q")
    print("\n[Paper4] reproduction workflow completed successfully.")


if __name__ == "__main__":
    main()
