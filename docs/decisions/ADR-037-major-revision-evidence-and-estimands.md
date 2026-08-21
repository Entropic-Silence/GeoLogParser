# ADR-037: Major-revision evidence tiers and primary estimands

Date: 2026-08-17  
Status: accepted

## Context

The first manuscript closure mixed strong accuracy evidence with weaker source-
agreement, metadata, Silver, and no-reference audits, and it treated some
interval-level observations as if they were independent. Paper II also lacked a
real same-candidate-pool component analysis, while Paper III's full-support
risk result confounded accepted-record value changes with document selection.

## Decision

1. Every main result declares one of five evidence tiers; Synthetic remains a
   separate controlled class.
2. Documents/boreholes are the primary uncertainty units. Interval pooling is
   descriptive unless dependence is otherwise modelled.
3. Paper I is a multi-cohort and cross-source evaluation, not a comprehensive
   multilingual benchmark. Fixed-prediction random/grouped resampling is only a
   diagnostic.
4. Paper II's primary component evidence is the v004/v005 identical-candidate-
   pool ablation. Correction safety is reported primarily per accepted document;
   action-level iid bounds are secondary.
5. Paper III reports both full-support and strict matched-subset estimands,
   spatial-support geometry, IDW sensitivity, and leave-one-borehole-out error.
   It is a sensitivity diagnostic, not validation of geological interpretation.
6. Project-log branches, no-GT audits, and software interoperability smoke tests
   move to supplementary material while their artifacts remain indexed.

## Consequences

- The Paper III matched-subset result is a negative but decisive finding: risk-
  aware selection does not improve volume error over rereading on identical
  accepted records and is worse than raw under that estimand.
- Paper II's complete score is interpreted as a precision/recovery operating
  point, not evidence that every constraint independently improves F1.
- Three generated main-table files, numeric prose bindings, document-level
  public outputs, and CI regeneration checks become mandatory publication
  artifacts.
