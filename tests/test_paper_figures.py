import json
from pathlib import Path

from geologparser.paper_figures import save_degradation_profiles, save_method_schematic, save_padova_locations


def test_paper_figure_writers_create_nonempty_files(tmp_path: Path):
    degradation = tmp_path / "degradation.jsonl"
    degradation.write_text("\n".join([
        json.dumps({"profile": "blur_1"}), json.dumps({"profile": "blur_1"}),
        json.dumps({"profile": "noise_1"}),
    ]) + "\n")
    locations = tmp_path / "locations.jsonl"
    locations.write_text("\n".join([
        json.dumps({"link_key": "GS1", "longitude": 10, "latitude": 44}),
        json.dumps({"link_key": "PS1", "longitude": 11, "latitude": 44.5}),
        json.dumps({"link_key": "TS2", "longitude": 13, "latitude": 45.5}),
    ]) + "\n")
    outputs = [tmp_path / "d.png", tmp_path / "l.png", tmp_path / "m.png"]
    save_degradation_profiles(degradation, outputs[0])
    save_padova_locations(locations, outputs[1])
    save_method_schematic(outputs[2])
    assert all(path.stat().st_size > 1000 for path in outputs)
