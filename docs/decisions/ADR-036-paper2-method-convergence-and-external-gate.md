# ADR-036: Paper II method convergence and external gate

Date: 2026-08-16  
Status: Accepted

## Decision

Stop Qwen3.8/NVFP4 training work and stop adding unsupported local heuristics.
Paper II is frozen around the v028 routed structural parser with the validated
native positioned-text expert, page-family routing, field-specific evidence,
deterministic geometry, non-mutating geological constraints, and calibrated
accept/abstain decisions.

The immutable configuration is
`configs/experiments/paper2/P2_CONVERGED_METHOD_V001.yaml`. Its external gate
uses round, predeclared development requirements rather than thresholds chosen
from BGS v003. The requirements are:

- mean nested Boundary F1 at least 0.30;
- mean nested Interval F1 at least 0.15;
- positive Interval F1 in at least four of five source-disjoint folds;
- overall boundary CNER no more than 0.35;
- independent selective precision at least 0.95;
- independent coverage at least 0.25;
- independent selective CNER no more than 0.05.

If all gates pass, BGS v003 may be evaluated once. Its result cannot be used to
change thresholds, prompts, page-family aliases, parser logic, or model
parameters. Because v003 is small, it is external confirmation evidence rather
than the sole basis for a generalization claim.

## Existing evidence used by the gate

The BGS v001 nested development mean is Boundary F1 0.3333 and Interval F1
0.1841, with four of five folds having non-zero Interval F1. Overall v028
Boundary F1 is 0.3475 and boundary CNER is 0.3281. The independent Swissgeol
risk validation accepts 15/35 documents (coverage 0.4286) with observed
selective precision 1.0000 and CNER 0.0000. The Swiss split was previously
inspected and is validation, not untouched confirmation.

## Protocol deviation record

During preparation, a SHA-256 command read the raw bytes of the BGS v003
manifest before this ADR was committed. No JSON was parsed, no record IDs,
pages, interval labels, source titles, or error cases were displayed, and no
method decision was based on its contents. The hash-only access is nevertheless
recorded as a protocol deviation. Semantic evaluation remains limited to the
single post-freeze run, but the manuscript must not state that the manifest
file was literally never opened before freezing.

## Consequences

- Paper II development is closed except for reproducibility fixes that do not
  alter predictions.
- Paper I moves to evidence and publication-readiness audit.
- Paper III becomes the main active experimental track.
- Human-efficiency claims remain unavailable until actual timed sessions exist;
  software timing is not substituted for human time.
