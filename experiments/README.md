# Experiment records

Each run uses `results/YYYY-MM-DD/EXPERIMENT_ID/` and writes, at minimum:

- `run.yaml`: experiment ID, git commit, UTC date, dataset/split versions,
  model and revision, prompt version, seed, hardware/software, and config.
- `metrics.json`
- `predictions.jsonl`
- `errors.jsonl`
- `run.log`

Result directories are immutable. A rerun receives a new experiment ID.

