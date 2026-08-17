"""OpenAI-compatible Responses transport for auditable multimodal runs."""

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


class OpenAIResponsesVLMAdapter(VLMAdapter):
    """Use the Responses image-input schema without provider-specific prompting."""

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str,
        model_revision: str,
        api_key_env: str | None,
        max_tokens: int = 1024,
        timeout_seconds: float = 300.0,
        temperature: float | None = None,
        request_options: Mapping[str, Any] | None = None,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be an HTTP(S) URL")
        if not model_id:
            raise ValueError("model_id is required")
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.model_revision = model_revision
        self.api_key_env = api_key_env
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.request_options = dict(request_options or {})

    @staticmethod
    def _image_url(path: Path) -> str:
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{media_type};base64,{encoded}"

    @staticmethod
    def _output_text(body: Mapping[str, Any]) -> str:
        direct = body.get("output_text")
        if isinstance(direct, str):
            return direct
        parts: list[str] = []
        for output in body.get("output", []):
            if not isinstance(output, Mapping):
                continue
            for content in output.get("content", []):
                if isinstance(content, Mapping) and content.get("type") == "output_text":
                    text = content.get("text")
                    if isinstance(text, str):
                        parts.append(text)
        return "".join(parts)

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
        credential = os.environ.get(self.api_key_env) if self.api_key_env else None
        if self.api_key_env and not credential:
            raise RuntimeError(f"required credential environment variable is unset: {self.api_key_env}")
        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        content.extend(
            {"type": "input_image", "image_url": self._image_url(path)}
            for path in images
        )
        payload: dict[str, Any] = {
            "model": self.model_id,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        payload.update(self.request_options)
        headers = {"Content-Type": "application/json"}
        if credential:
            headers["Authorization"] = f"Bearer {credential}"
        request = Request(
            f"{self.base_url}/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(800).decode("utf-8", "replace")
            raise RuntimeError(f"VLM Responses endpoint returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"VLM Responses endpoint is unavailable: {exc.reason}") from exc
        elapsed = time.perf_counter() - started
        usage = body.get("usage") or {}
        output_tokens = usage.get("output_tokens")
        return VLMGeneration(
            text=self._output_text(body),
            latency_seconds=elapsed,
            input_image_count=len(images),
            prompt_version=prompt_version,
            model_id=str(body.get("model") or self.model_id),
            model_revision=self.model_revision,
            peak_gpu_memory_bytes=None,
            output_tokens=int(output_tokens) if isinstance(output_tokens, int) else None,
            hit_max_new_tokens=(int(output_tokens) >= self.max_tokens) if isinstance(output_tokens, int) else None,
            generation_config={
                "transport": "openai_responses",
                "endpoint": self.base_url,
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "request_options": self.request_options,
                "input_tokens": usage.get("input_tokens"),
                "provider_response": {
                    "id": body.get("id"),
                    "model": body.get("model"),
                    "created": body.get("created_at") or body.get("created"),
                    "system_fingerprint": body.get("system_fingerprint"),
                    "service_tier": body.get("service_tier"),
                    "status": body.get("status"),
                    "incomplete_details": body.get("incomplete_details"),
                },
            },
        )
