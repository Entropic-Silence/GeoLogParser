from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_unix_resource_is_isolated_in_portable_adapter() -> None:
    offenders = []
    for base in (ROOT / "src", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            if path == ROOT / "src/geologparser/runtime_resources.py":
                continue
            text = path.read_text(encoding="utf-8")
            if re.search(r"(^|\n)\s*(?:import resource|from resource import)", text):
                offenders.append(path.relative_to(ROOT).as_posix())
            if "resource.getrusage" in text:
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
