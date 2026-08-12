"""Capture a refreshable, non-destructive environment report."""

from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False, timeout=20)
        raw = (completed.stdout or completed.stderr).strip()
        return "\n".join(line.rstrip() for line in raw.splitlines())
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"unavailable: {exc}"


def first_line(command: list[str]) -> str:
    output = run(command)
    return output.splitlines()[0] if output else "unavailable"


def main() -> None:
    packages = ["torch", "transformers", "vllm", "paddle", "paddleocr", "onnxruntime", "fitz", "pytesseract"]
    package_lines = [f"- `{name}`: {'installed' if importlib.util.find_spec(name) else 'not installed'}" for name in packages]
    tools = ["docker", "tesseract", "pdftotext", "nvcc", "ollama", "llama-cli"]
    versions = {
        "docker": first_line(["docker", "--version"]),
        "tesseract": first_line(["tesseract", "--version"]),
        "pdftotext": first_line(["pdftotext", "-v"]),
        "nvcc": first_line(["nvcc", "--version"]),
        "ollama": first_line(["ollama", "--version"]),
        "llama-cli": first_line(["llama-cli", "--version"]),
    }
    tool_lines = [f"- `{name}`: `{shutil.which(name) or 'not found'}`; {versions[name]}" for name in tools]
    report = f"""# Environment report

- Captured (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
- Host: `{platform.node()}`
- OS: `{platform.platform()}`
- Python: `{platform.python_version()}` at `{shutil.which('python3')}`

## CPU and memory

```text
{run(['lscpu'])}
{run(['free', '-h'])}
```

## GPU

```text
{run(['nvidia-smi', '--query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu', '--format=csv,noheader'])}
```

No GPU was paused for this report. Utilization is a point-in-time observation.

## Disk

```text
{run(['lsblk', '-o', 'NAME,TYPE,FSTYPE,SIZE,ROTA,MOUNTPOINTS,MODEL'])}
{run(['df', '-hT', '/root', '/data'])}
```

Large assets go to `/data/GeoLogParser`; code and latency-sensitive small files
remain at `/root/GeoLogParser`.

## Python AI/document packages

{chr(10).join(package_lines)}

## External runtimes

{chr(10).join(tool_lines)}

## Locally observed model assets

- `/data/LLM` contains about 455 GB of text-LLM assets, including Qwen-family
  FP8 directories and one GGUF text LLM observed in the bounded scan.
- Numerous image/video diffusion weights and LoRAs exist under `/data`.
- No complete Chinese document OCR, layout, or document-VLM checkpoint was
  identified by the bounded scan on 2026-08-12.
- Exact reusable model inventory and license audit: `TBD` before model baseline.

## Compatibility and operational risks

1. NVIDIA driver is visible, but `nvcc` is not on the host PATH; each selected
   PyTorch/Paddle/vLLM build must be checked against its bundled CUDA runtime and
   this new GPU/driver combination.
2. The host system Python lacks the project ML stack. A project `.venv` now
   contains the lightweight test environment; use a versioned model container or
   dedicated extra for heavier runtimes and do not mutate unrelated environments.
3. All five GPUs were at 100% utilization from mining during the snapshot.
   Schedule one explicit card for inference, pause only that worker, log the
   action, and restore it after use.
4. RTX 5090 and RTX 2080 Ti have different compute generations. A single wheel/
   kernel stack may not be optimal or compatible across both; test adapters per
   hardware class.
5. `/data` is a mechanical RAID5 volume: suitable for large immutable assets,
   but page crops and random-access training shards may need an SSD staging
   cache with bounded retention.
6. Tesseract 4.1.1, `chi_sim`, and Poppler 22.02.0 were installed during the
   foundation round. Their age makes them a smoke-test baseline, not an assumed
   competitive OCR system.
"""
    (ROOT / "docs" / "environment_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
