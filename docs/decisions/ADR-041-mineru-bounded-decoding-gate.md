# ADR-041: MinerU2.5 bounded-decoding feasibility gate

Date: 2026-08-17

## Observation

The first California v001 MinerU2.5-Pro run used the official two-step parser
with its library defaults.  The installed Transformers client maps an unset
`max_new_tokens` to the model context length.  After more than three hours on
an RTX 5090 it had produced no serialised page result, no checkpoint and no
usable formal artifact, while occupying the GPU.  The run was terminated; it
is not scored or indexed.

## Decision

Do not interpret the terminated run as a model result.  A replacement smoke
must use the same official two-step interface with recorded, stage-specific
generation budgets: 2,048 new tokens for layout, 4,096 for tables and 1,024
for other content.  The smoke is a runtime and decoder feasibility test, not
a Gold benchmark or a tuning exercise.

## Gate

The one-page bounded smoke completed in 138.25 s and serialised 80 page
elements, including five table elements, but the fixed declared-top/bottom
decoder recovered zero intervals from 22 references.  This is enough to fail
the feasibility gate: expanding the run would consume several hours while
providing no evidence of a usable numerical interface.

MinerU therefore remains a registered but unavailable comparison for this
protocol.  The stopped unbounded run and the one-page smoke are not formal
benchmarks and support no performance claim.
