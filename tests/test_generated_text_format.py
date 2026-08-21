from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_committed_publication_text_artifacts_are_utf8_lf() -> None:
    subprocess.run(
        [sys.executable, "scripts/audit_generated_text_format.py"],
        cwd=ROOT,
        check=True,
    )
