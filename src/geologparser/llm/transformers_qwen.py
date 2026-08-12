"""Text-only inference through the locally frozen Qwen3-VL language stack."""

from __future__ import annotations

import time
from pathlib import Path

from .base import LLMAdapter, LLMGeneration


class Qwen3VLTextTransformersAdapter(LLMAdapter):
    def __init__(self, model_path: Path, *, model_id: str, model_revision: str, max_new_tokens: int = 1536):
        if not model_path.is_dir():
            raise FileNotFoundError(model_path)
        self.model_path = model_path
        self.model_id = model_id
        self.model_revision = model_revision
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._processor = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        except ImportError as exc:
            raise RuntimeError("text LLM audit requires the locked VLM runtime") from exc
        if not torch.cuda.is_available():
            raise RuntimeError("local text LLM audit requires CUDA")
        self._model = Qwen3VLForConditionalGeneration.from_pretrained(
            str(self.model_path), dtype=torch.bfloat16, device_map={"": 0},
            local_files_only=True, attn_implementation="sdpa",
        ).eval()
        self._processor = AutoProcessor.from_pretrained(str(self.model_path), local_files_only=True)

    def generate(self, text: str, prompt: str, *, prompt_version: str) -> LLMGeneration:
        if not text.strip():
            raise ValueError("text-only LLM input is empty")
        self._load()
        import torch

        messages = [{"role": "user", "content": [{"type": "text", "text": f"{prompt}\n\nSOURCE TEXT:\n{text}"}]}]
        inputs = self._processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt",
        ).to(self._model.device)
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        with torch.inference_mode():
            generated_output = self._model.generate(
                **inputs, max_new_tokens=self.max_new_tokens, do_sample=False,
                use_cache=True, return_dict_in_generate=True,
            )
        elapsed = time.perf_counter() - started
        generated = generated_output.sequences
        trimmed = [output[len(input_ids):] for input_ids, output in zip(inputs.input_ids, generated)]
        output_tokens = int(trimmed[0].numel())
        response = self._processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False,
        )[0]
        return LLMGeneration(
            text=response, latency_seconds=elapsed, prompt_version=prompt_version,
            model_id=self.model_id, model_revision=self.model_revision,
            input_tokens=int(inputs.input_ids[0].numel()), output_tokens=output_tokens,
            peak_gpu_memory_bytes=int(torch.cuda.max_memory_allocated()),
            hit_max_new_tokens=output_tokens >= self.max_new_tokens,
            generation_config={"do_sample": False, "max_new_tokens": self.max_new_tokens, "dtype": "bfloat16", "attention": "sdpa"},
        )
