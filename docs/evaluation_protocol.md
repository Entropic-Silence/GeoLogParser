# Evaluation API and protocol

## Levels

1. Character: CER, WER, and a separately reported numeric CER (`TBD` adapter).
2. Field: exact match for identifiers/categories; MAE and threshold accuracy for
   numeric fields; normalized description similarity (`TBD` method).
3. Interval: precision/recall/F1 under an explicit matching strategy; top,
   bottom, and thickness MAE; boundary accuracy at ±0.01/0.05/0.10 m.
4. Geology: report each constraint rate separately. An aggregate GCR remains
   experimental and must not hide constraint coverage or severity.

## Missingness and denominators

Every metric output stores numerator and denominator. Missing prediction is an
error for extraction coverage metrics; numeric MAE currently evaluates paired
non-null values and must be reported together with coverage. Empty denominators
produce `null`, never zero. Dataset aggregation must be micro/macro-labelled.

## Interval matching

The paper-facing v001 strategy is
`order_preserving_max_cardinality_then_min_error_v001`. A reference/prediction
pair is eligible only when both top- and bottom-boundary absolute errors are at
or below the configured inclusive tolerance. Dynamic programming maximizes the
number of matches and then minimizes the summed top+bottom boundary error.
Matches preserve depth order, so strata cannot cross. Intervals with a missing
top or bottom cannot match. Unmatched reference and prediction counts are
always emitted beside micro precision/recall/F1 and matched-boundary MAE.

The earlier exact-ID function remains an API-test helper only and is not
eligible for paper interval claims. Every experiment records the matching
strategy version and tolerance; primary tolerance is still `TBD` pending an
annotation-resolution study, while ±0.01/0.05/0.10 m remain required reports.

## Confidence

Confidence is evaluated against field correctness with Brier score, ECE, and a
reliability diagram. Bin count and binning strategy are part of run metadata.
Review/abstention evaluation additionally reports coverage, risk, review recall,
and auto-accept error rate.

## Proposed-method safety metrics

- Critical Numerical Error Rate: formal error threshold per field is `TBD`.
- False Correction Rate: incorrect automatic corrections / all automatic
  corrections, with correctness judged against ground truth.
- Manual Review Recall: erroneous fields sent to review / all erroneous fields.

No aggregate metric replaces its component results.

## Constraint coverage

The implemented audit summary computes `1 - violations/evaluated_checks` only
when at least one check was evaluated. With zero evaluated checks, consistency
is `null`, never 1.0. It separately emits document coverage (documents with any
evaluated constraint / all documents), total evaluated checks, total
violations, and per-constraint counts/rates. This is an audit statistic; the
final GCR definition remains `TBD` until constraint dependence, severity
weighting, and false-positive behavior have been validated on annotated data.
