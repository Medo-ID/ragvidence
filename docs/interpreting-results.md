# Interpreting results

Start with the report status and the data actually evaluated. Source-only reports
show ingestion/chunk diagnostics. Questions without reviewed references show
retrieval inspection. Neither supplies a relevance score or a quality winner.

## Sufficient evidence

With reviewed original-span references, a question passes only when the final
returned context covers every span of every required evidence item. Several
chunks can jointly cover an item; duplicated overlap does not add credit. A
matching source ID or a high ranking score alone does not establish sufficiency.

Evidence is scored after budgets and compression, so dropping a required
condition can turn a retrieval success into a failure. Workspace evaluations use
reviewed evidence IDs attached to source units; those labels cannot establish
that a shortened extract still contains the fact.

## Evidence coverage

Coverage is the fraction of required evidence items completely covered by the
returned context. Finding one of two required items gives 0.5 coverage and an
insufficient result. This is not the percentage of an answer that is correct.

## First relevant rank and reciprocal rank

For span evaluation, the first complete evidence rank is the earliest ranking
prefix whose combined context completes at least one required item. Reciprocal
rank is one divided by that rank, or zero when no item is complete. These metrics
do not establish that every required item was retrieved.

## Precision at k

Span precision counts returned hits overlapping required evidence spans, divided
by the configured `k`, even if fewer hits were returned. Overlap alone does not
establish full evidence coverage. Use precision alongside sufficiency and inspect
supporting context rather than optimizing this number alone.

## Improvements and regressions

- `fail_to_pass`: required evidence is now sufficient.
- `pass_to_fail`: required evidence was lost; investigate before adoption.
- `pass_to_pass`: sufficiency was preserved.
- `fail_to_fail`: required evidence is still incomplete.

Open the changed questions before accepting an aggregate improvement. Confirm the
source text, final context and evidence locations, then check that differences
are explained by the intended technique or setting. Compare the same original
questions and references under a declared depth or context-budget policy.

## Counts, uncertainty and resources

Check dev/heldout question counts and slice denominators. Unanswerable reviewed
questions have N/A retrieval-quality metrics; the CLI does not score abstention.
Small or unrepresentative samples do not establish a general winner. Intervals
can be unavailable when too few independent question groups were evaluated.

Use separate heldout questions after choosing settings on dev data. Repeatedly
consulting heldout results weakens that separation. Review timing, context size
and resource availability alongside evidence quality. Supplied usage/pricing is
an estimate; missing timing, token usage and cost stay unavailable.

## Make a decision

Prefer a technique whose observed trade-offs suit your application's questions,
context budget and operating constraints. Inspect failures as well as gains,
then validate the choice in your own system. Diagnostic explanations suggest a
next experiment; they do not establish a causal or universal quality guarantee.
Retrieval evidence does not establish generated-answer or citation correctness.
