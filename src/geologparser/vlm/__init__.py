"""Backend-neutral VLM inference and parsing APIs."""

from .base import VLMAdapter, VLMGeneration
from .parsing import compact_payload_to_record, parse_json_object
from .transformers_qwen import Qwen3VLTransformersAdapter

__all__ = [
    "Qwen3VLTransformersAdapter", "VLMAdapter", "VLMGeneration",
    "compact_payload_to_record", "parse_json_object",
]
