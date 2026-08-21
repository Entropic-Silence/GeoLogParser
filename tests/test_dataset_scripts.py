import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def test_build_dataset_script_creates_disjoint_and_random_manifests(tmp_path):
    manifest = tmp_path / "records.jsonl"
    rows = [
        {"record_id": f"R{i}", "project_id": f"P{i//2}", "template_id": f"T{i//3}", "source_id": f"S{i//4}"}
        for i in range(12)
    ]
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows))
    output = tmp_path / "splits"
    subprocess.run([
        sys.executable, str(ROOT / "scripts/build_dataset.py"),
        str(manifest), str(output),
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    assert json.loads((output / "summary.json").read_text(encoding="utf-8"))["records"] == 12
    assert (output / "project_disjoint_v001.json").is_file()
    assert (output / "template_disjoint_v001.json").is_file()


def test_preprocess_script_writes_output_and_metadata(tmp_path):
    source, destination, metadata = tmp_path / "in.png", tmp_path / "out.jpg", tmp_path / "meta.json"
    Image.new("RGB", (40, 20), "white").save(source)
    subprocess.run([
        sys.executable, str(ROOT / "scripts/preprocess.py"),
        str(source), str(destination), "--jpeg-quality", "50", "--metadata", str(metadata),
    ], cwd=ROOT, check=True, capture_output=True, text=True)
    assert destination.is_file()
    assert json.loads(metadata.read_text(encoding="utf-8"))["parameters"]["jpeg_quality"] == 50
