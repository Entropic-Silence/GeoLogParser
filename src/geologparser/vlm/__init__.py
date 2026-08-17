"""Backend-neutral VLM inference and parsing APIs."""

from .base import VLMAdapter, VLMGeneration
from .parsing import compact_payload_to_record, parse_json_object
from .openai_compatible import OpenAICompatibleVLMAdapter
from .anthropic_messages import AnthropicMessagesVLMAdapter
from .mineru_tables import decode_mineru_intervals
from .transformers_qwen import Qwen3VLTransformersAdapter

__all__ = [
    "AnthropicMessagesVLMAdapter", "OpenAICompatibleVLMAdapter", "Qwen3VLTransformersAdapter", "VLMAdapter", "VLMGeneration",
    "compact_payload_to_record", "decode_mineru_intervals", "parse_json_object",
]
