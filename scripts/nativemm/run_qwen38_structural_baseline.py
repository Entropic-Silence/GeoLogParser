#!/usr/bin/env python3
"""Run a small Qwen3.8-27B FP8 structural-graph baseline through vLLM.

This is an exploratory, source-disjoint development audit. It never opens
BGS v002/v003 and never feeds reference intervals or OCR-derived candidates to
the model. The API key is read only from ``VLLM_API_KEY``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import time

import requests


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts/native_mm_qwen38_structural_graph_v001.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_json(content: str) -> dict | None:
    content = content.strip()
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(content[start:end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--record-id", action="append", required=True)
    parser.add_argument("--page", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18000")
    parser.add_argument("--model", default="qwen38-fp8-tp4-mtp4-long")
    parser.add_argument("--max-new-tokens", type=int, default=1800)
    args = parser.parse_args()
    if len(args.record_id) != len(args.page):
        raise SystemExit("--record-id and --page must be repeated the same number of times")
    api_key = __import__("os").environ.get("VLLM_API_KEY")
    if not api_key:
        raise SystemExit("VLLM_API_KEY is required and is not persisted by this script")
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    session = requests.Session()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = []
    for record_id, page in zip(args.record_id, args.page):
        image_path = args.source_run / f"{record_id}_page-{page}.png"
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
            ]}],
            "temperature": 0.0,
            "max_tokens": args.max_new_tokens,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        started = time.perf_counter()
        response = session.post(
            f"{args.base_url.rstrip('/')}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
        elapsed = time.perf_counter() - started
        response.raise_for_status()
        body = response.json()
        message = body.get("choices", [{}])[0].get("message", {})
        content = str(message.get("content") or "")
        graph = extract_json(content)
        rows.append({
            "record_id": record_id,
            "page": page,
            "image_path": str(image_path),
            "image_sha256": sha256(image_path),
            "model": args.model,
            "endpoint": args.base_url,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "http_status": response.status_code,
            "latency_seconds": elapsed,
            "prompt_tokens": body.get("usage", {}).get("prompt_tokens"),
            "completion_tokens": body.get("usage", {}).get("completion_tokens"),
            "json_valid": graph is not None,
            "structural_evidence_count": sum(len(graph.get(key, [])) for key in ("regions", "columns", "events")) if graph else 0,
            "graph": graph,
            "raw_content": content,
            "finish_reason": body.get("choices", [{}])[0].get("finish_reason"),
        })
        print(json.dumps({"record_id": record_id, "page": page, "json_valid": graph is not None, "latency_seconds": elapsed}, ensure_ascii=False))
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
