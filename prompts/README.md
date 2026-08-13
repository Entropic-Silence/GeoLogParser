# Prompt registry

Every VLM/LLM prompt is immutable once used by an indexed run. Experiments
record both the version and content SHA256.

- `vlm_extract_v001.md`: B4 zero-shot structured extraction engineering audits.
- `vlm_extract_fewshot_v001.md`: B5 few-shot engineering audit.
- `llm_extract_v001.md`: B2 text-channel engineering audit.
- `constraint_reread_numeric_v001.md`: strict field-ROI numeric transcription;
  uncalibrated VLM tokens have no confidence/bbox and uncertain tokens are
  withheld from candidate ranking.

None of these audit uses establishes benchmark accuracy without human Ground
Truth. Prompt revisions require a new versioned file and experiment ID.
