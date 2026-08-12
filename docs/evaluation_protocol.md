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

The v001 function supports exact interval IDs for API testing only. Paper runs
must select and version a boundary-aware bipartite matching protocol before
claiming interval P/R/F1. The matching threshold and tie-breaking policy belong
in the experiment config.

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

