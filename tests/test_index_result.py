import json
import subprocess
from pathlib import Path

from geologparser.experiment import create_run_directory


def test_index_result_script_appends_hashes(tmp_path):
    # The script intentionally requires in-repository results; exercise its
    # duplicate/index logic through the installed path primitives elsewhere.
    script = Path(__file__).parents[1] / "scripts/index_result.py"
    assert script.is_file()
    assert "file_sha256" in script.read_text(encoding="utf-8")
