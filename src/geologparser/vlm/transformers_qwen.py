"""Local Hugging Face Transformers adapter for Qwen3-VL."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Sequence

from .base import VLMAdapter, VLMGeneration


class Qwen3VLTransformersAdapter(VLMAdapter):
    """Greedy single-GPU inference with a fixed local model snapshot."""

    def __init__(
        self,
        model_path: Path,
        *,
        model_id: str,
        model_revision: str,
        max_new_tokens: int = 2048,
        min_pixels: int = 256 * 28 * 28,
        max_pixels: int = 1280 * 28 * 28,
    ) -> None:
        if not model_path.is_dir():
            raise FileNotFoundError(f"local VLM snapshot not found: {model_path}")
        self.model_path = model_path
        self.model_id = model_id
        self.model_revision = model_revision
        self.max_new_tokens = max_new_tokens
        self.min_pixels = min_pixels
        self.max_pixels = max_pixels
        self._model = None
        self._processor = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        except ImportError as exc:
            raise RuntimeError(
                "Qwen3-VL inference requires the locked VLM runtime; see requirements-vlm.txt"
            ) from exc
        if not torch.cuda.is_available():
            raise RuntimeError("Qwen3-VL audit requires an available CUDA GPU")
        self._model = Qwen3VLForConditionalGeneration.from_pretrained(
            str(self.model_path),
            dtype=torch.bfloat16,
            device_map={"": 0},
            local_files_only=True,
            attn_implementation="sdpa",
        ).eval()
        self._processor = AutoProcessor.from_pretrained(
            str(self.model_path),
            local_files_only=True,
            min_pixels=self.min_pixels,
            max_pixels=self.max_pixels,
        )

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
        self._load()
        import torch
        from PIL import Image

        pil_images = []
        try:
            pil_images = [Image.open(path).convert("RGB") for path in images]
            content: list[dict[str, Any]] = [
                {"type": "image", "image": image} for image in pil_images
            ] + [{"type": "text", "text": prompt}]
            messages = [{"role": "user", "content": content}]
            inputs = self._processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self._model.device)
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            with torch.inference_mode():
                generated_output = self._model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    use_cache=True,
                    return_dict_in_generate=True,
                )
            elapsed = time.perf_counter() - started
            generated = generated_output.sequences
            trimmed = [output[len(input_ids) :] for input_ids, output in zip(inputs.input_ids, generated)]
            output_tokens = int(trimmed[0].numel())
            text = self._processor.batch_decode(
                trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False,
            )[0]
            peak = int(torch.cuda.max_memory_allocated())
            return VLMGeneration(
                text=text,
                latency_seconds=elapsed,
                input_image_count=len(images),
                prompt_version=prompt_version,
                model_id=self.model_id,
                model_revision=self.model_revision,
                peak_gpu_memory_bytes=peak,
                output_tokens=output_tokens,
                hit_max_new_tokens=output_tokens >= self.max_new_tokens,
                generation_config={
                    "do_sample": False,
                    "max_new_tokens": self.max_new_tokens,
                    "min_pixels": self.min_pixels,
                    "max_pixels": self.max_pixels,
                    "dtype": "bfloat16",
                    "attention": "sdpa",
                },
            )
        finally:
            for image in pil_images:
                image.close()
