from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from geologparser.vlm import OpenAICompatibleVLMAdapter


class FakeResponse:
    def __init__(self, body: dict):
        self.body = body

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_openai_compatible_adapter_sends_image_and_records_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    image = tmp_path / "page.png"
    image.write_bytes(b"png-bytes")
    monkeypatch.setenv("TEST_VLM_KEY", "secret")
    adapter = OpenAICompatibleVLMAdapter(
        base_url="http://127.0.0.1:18000",
        model_id="example-vlm",
        model_revision="rev-1",
        api_key_env="TEST_VLM_KEY",
        max_tokens=64,
        request_options={"chat_template_kwargs": {"enable_thinking": False}},
    )
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"model": "served-model", "choices": [{"message": {"content": "{}"}}], "usage": {"prompt_tokens": 11, "completion_tokens": 3}})

    with patch("geologparser.vlm.openai_compatible.urlopen", fake_urlopen):
        output = adapter.generate([image], "read the page", prompt_version="p1")

    assert captured["url"] == "http://127.0.0.1:18000/v1/chat/completions"
    assert captured["payload"]["model"] == "example-vlm"
    assert captured["payload"]["messages"][0]["content"][1]["type"] == "image_url"
    assert captured["payload"]["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert output.model_id == "served-model"
    assert output.output_tokens == 3
    assert output.generation_config["prompt_tokens"] == 11


def test_openai_compatible_adapter_requires_declared_credential(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    image = tmp_path / "page.png"
    image.write_bytes(b"png-bytes")
    monkeypatch.delenv("MISSING_VLM_KEY", raising=False)
    adapter = OpenAICompatibleVLMAdapter(
        base_url="http://127.0.0.1:18000",
        model_id="example-vlm",
        model_revision="rev-1",
        api_key_env="MISSING_VLM_KEY",
    )
    with pytest.raises(RuntimeError, match="MISSING_VLM_KEY"):
        adapter.generate([image], "read", prompt_version="p1")
