from pathlib import Path

from geologparser.rereading import VLMNumericROIAdapter, numeric_candidates_from_regions
from geologparser.vlm import VLMGeneration


class FakeVLM:
    def __init__(self, text: str):
        self.text = text

    def generate(self, images, prompt, *, prompt_version):
        assert len(images) == 1
        assert prompt == "read numbers"
        return VLMGeneration(
            text=self.text, latency_seconds=0.2, input_image_count=1,
            prompt_version=prompt_version, model_id="fake", model_revision="r1",
            peak_gpu_memory_bytes=12, output_tokens=8, hit_max_new_tokens=False,
        )


def test_vlm_roi_reader_returns_strict_uncalibrated_numeric_regions(tmp_path: Path):
    image = tmp_path / "roi.png"
    image.write_bytes(b"fixture")
    reader = VLMNumericROIAdapter(
        FakeVLM('{"numeric_tokens":["-5,80","4.50"],"uncertain":false}'),
        "read numbers", prompt_version="v1",
    )
    output = reader.read(image)
    assert [region.text for region in output.regions] == ["-5,80", "4.50"]
    assert all(region.confidence is None and region.bbox is None for region in output.regions)
    assert output.audit["parse_status"] == "valid"
    assert output.audit["confidence_policy"] == "none_uncalibrated"
    candidates = numeric_candidates_from_regions(output.regions, reader.name)
    assert [candidate.value for candidate in candidates] == [-5.8, 4.5]
    assert all(candidate.pixel_evidence is None for candidate in candidates)
    assert all(candidate.layout_confidence is None for candidate in candidates)


def test_vlm_roi_reader_rejects_explanation_and_returns_no_candidate(tmp_path: Path):
    image = tmp_path / "roi.png"
    image.write_bytes(b"fixture")
    reader = VLMNumericROIAdapter(
        FakeVLM('{"numeric_tokens":["likely 4.50"],"uncertain":true}'),
        "read numbers", prompt_version="v1",
    )
    output = reader.read(image)
    assert output.regions == ()
    assert output.audit["parse_status"] == "failed"
    assert "non-numeric token" in output.audit["parse_error"]


def test_vlm_roi_reader_rejects_extra_schema_fields(tmp_path: Path):
    image = tmp_path / "roi.png"
    image.write_bytes(b"fixture")
    reader = VLMNumericROIAdapter(
        FakeVLM('{"numeric_tokens":["4.50"],"uncertain":false,"guess":4.5}'),
        "read numbers", prompt_version="v1",
    )
    output = reader.read(image)
    assert output.regions == ()
    assert "only numeric_tokens and uncertain" in output.audit["parse_error"]


def test_vlm_roi_reader_audits_but_withholds_uncertain_numeric_tokens(tmp_path: Path):
    image = tmp_path / "roi.png"
    image.write_bytes(b"fixture")
    reader = VLMNumericROIAdapter(
        FakeVLM('{"numeric_tokens":["4.50"],"uncertain":true}'),
        "read numbers", prompt_version="v1",
    )
    output = reader.read(image)
    assert output.regions == ()
    assert output.audit["parse_status"] == "valid"
    assert output.audit["numeric_tokens"] == ["4.50"]
    assert output.audit["candidate_policy"] == "withheld_uncertain"
