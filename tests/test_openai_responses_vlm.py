from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from geologparser.vlm import OpenAIResponsesVLMAdapter


class FakeResponse:
    def __init__(self, body: dict):
        self.body = body

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_openai_responses_adapter_sends_image_and_records_provider_metadata(tmp_path: Path, monkeypatch):
    image = tmp_path / "page.png"
    image.write_bytes(b"png-bytes")
    monkeypatch.setenv("TEST_RESPONSES_KEY", "secret")
    adapter = OpenAIResponsesVLMAdapter(
        base_url="http://127.0.0.1:18001",
        model_id="example-vlm",
        model_revision="revision-1",
        api_key_env="TEST_RESPONSES_KEY",
        max_tokens=64,
        temperature=None,
        request_options={"reasoning": {"effort": "high"}},
    )
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({
            "id": "resp-example",
            "model": "served-vlm",
            "status": "completed",
            "output": [{"content": [{"type": "output_text", "text": "{\"intervals\":[]}"}]}],
            "usage": {"input_tokens": 11, "output_tokens": 3},
        })

    with patch("geologparser.vlm.openai_responses.urlopen", fake_urlopen):
        output = adapter.generate([image], "read the page", prompt_version="p1")

    assert captured["url"] == "http://127.0.0.1:18001/v1/responses"
    assert captured["payload"]["model"] == "example-vlm"
    assert captured["payload"]["input"][0]["content"][1]["type"] == "input_image"
    assert captured["payload"]["reasoning"] == {"effort": "high"}
    assert "temperature" not in captured["payload"]
    assert output.model_id == "served-vlm"
    assert output.generation_config["provider_response"]["id"] == "resp-example"
