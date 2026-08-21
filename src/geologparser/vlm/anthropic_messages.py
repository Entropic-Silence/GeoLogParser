"""Official Anthropic Messages API adapter for auditable VLM benchmark runs.

The adapter mirrors the benchmark-neutral contract used by the OpenAI-compatible
adapter. It retains the provider-returned model identifier and never writes a
credential to a run artifact.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import VLMAdapter, VLMGeneration


class AnthropicMessagesVLMAdapter(VLMAdapter):
    """Greedy image inference through Anthropic's official Messages endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str,
        model_revision: str,
        api_key_env: str,
        max_tokens: int = 1024,
        timeout_seconds: float = 300.0,
        temperature: float = 0.0,
        anthropic_version: str = "2023-06-01",
        request_options: Mapping[str, Any] | None = None,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be an HTTP(S) URL")
        if not model_id:
            raise ValueError("model_id is required")
        if not api_key_env:
            raise ValueError("api_key_env is required")
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.model_revision = model_revision
        self.api_key_env = api_key_env
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.anthropic_version = anthropic_version
        self.request_options = dict(request_options or {})

    @staticmethod
    def _image_block(path: Path) -> dict[str, Any]:
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(path.read_bytes()).decode("ascii"),
            },
        }

    def generate(
        self,
        images: Sequence[Path],
        prompt: str,
        *,
        prompt_version: str,
    ) -> VLMGeneration:
        if not images:
            raise ValueError("at least one image is required")
        missing = [str(path) for path in images if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"missing input images: {missing}")
        credential = os.environ.get(self.api_key_env)
        if not credential:
            raise RuntimeError(f"required credential environment variable is unset: {self.api_key_env}")
        content = [self._image_block(path) for path in images]
        content.append({"type": "text", "text": prompt})
        payload: dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": content}],
        }
        payload.update(self.request_options)
        request = Request(
            f"{self.base_url}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": credential,
                "anthropic-version": self.anthropic_version,
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(800).decode("utf-8", "replace")
            raise RuntimeError(f"Anthropic endpoint returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Anthropic endpoint is unavailable: {exc.reason}") from exc
        elapsed = time.perf_counter() - started
        text = "".join(
            str(part.get("text") or "")
            for part in body.get("content", [])
            if isinstance(part, Mapping) and part.get("type") == "text"
        )
        usage = body.get("usage") or {}
        output_tokens = usage.get("output_tokens")
        return VLMGeneration(
            text=text,
            latency_seconds=elapsed,
            input_image_count=len(images),
            prompt_version=prompt_version,
            model_id=str(body.get("model") or self.model_id),
            model_revision=self.model_revision,
            output_tokens=int(output_tokens) if isinstance(output_tokens, int) else None,
            hit_max_new_tokens=(int(output_tokens) >= self.max_tokens) if isinstance(output_tokens, int) else None,
            generation_config={
                "transport": "anthropic_messages",
                "endpoint": self.base_url,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "anthropic_version": self.anthropic_version,
                "request_options": self.request_options,
                "input_tokens": usage.get("input_tokens"),
            },
        )
