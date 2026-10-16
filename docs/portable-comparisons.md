# Compare techniques on your data

Available in development builds; no new PyPI release has been published. Install a
development wheel as a tool, then invoke `ragvi` from any directory. In a source
checkout, prefix examples with `uv run`.

```bash
ragvi compare-data ./data --query "How do I reset pairing?"
ragvi compare-data ./data --questions questions.json --techniques bm25,semantic,hybrid
ragvi compare-data ./manual.md --reviewed reviewed.json --techniques bm25,parent-child
```

Default techniques are BM25 and parent-child, requiring no model. Data is loaded
and frozen once. Every configuration receives the same original documents and
questions. Chunk grids rematerialize passages from those originals without reading
or parsing the source files again. Source IDs and reviewed evidence remain stable.

The terminal and self-contained HTML report show configuration settings, observed
gains/regressions/ties, ranked passages, source locations, stage traces, resource
measurements and limitations. Repeat `--format html --format json --format markdown`
to choose exports; HTML is the default. No browser opens unless `--open` is supplied.
Every comparison and export receives a new directory; existing artifacts stay intact.

Use [portable techniques](portable-techniques.md) for provider settings, supported
data types, reviewed span references, query variants, prefixes and model prerequisites.
The [advanced techniques](portable-advanced-techniques.md) add metadata filters,
MMR, automatic rewriting and exact-span compression. These can be selected as
technique entries or composed explicitly in each suite variant's nested options.
Local models can download on first use; remote data transmission is disclosed.
Questions, reviewed references, selected sidecars, output/cache roots and marked
previous runs are excluded from folder ingestion.

## What the report can establish

Unreviewed questions produce an **unscored comparison**: actual contexts and resource
differences are available, but quality metrics and a quality winner are unavailable.
Without questions, reports explicitly say retrieval was not executed.

With `--reviewed`, complete unions of original evidence spans determine sufficiency
and coverage. Reports include reciprocal rank and precision, answerable denominators,
per-question evidence gained/lost/missing, and separate dev/heldout/slice summaries.
Unanswerable questions remain outside retrieval-quality rates. Answers and abstention
are not evaluated; nDCG is unavailable without reviewed relevance gains.

The report does not choose a universally best technique. Improvements, regressions,
neutral outcomes and keeping the baseline are valid results. Diagnosis is limited to
observed stages and cases; it does not claim what caused a failure.

## Existing RAG baseline

```bash
ragvi compare-data ./data --reviewed reviewed.json --results existing-results.jsonl --techniques bm25,hybrid
```

`existing` becomes the default baseline. `--baseline NAME` selects another named
configuration. Results use the exact-span or ID-only schemas documented in the
technique guide. A file may include both dev and heldout questions; all supplied hits
are validated, and only the selected phase is evaluated. Unknown questions still fail.

ID-only results are explicitly **registered-unit proxies**. Their derived numbers
cannot establish actual external-context quality, and quality threshold matches
remain unknown. Missing imported timing is N/A; it is never replaced with zero.
External internal-stage traces and indexing time remain unavailable.

## Comparison policies

| Policy | Requirement and interpretation |
| --- | --- |
| `fixed_k` (default) | Same maximum final k. Context volume may differ, especially for parents. |
| `fixed_tokens` | Same positive context budget and identical identified tokenizer. Final k may differ. |
| `descriptive` | Different depths/budgets are allowed as explicit trade-offs. |

Set `--policy` or the suite's `policy`. Invalid policies fail before retrieval/model
execution. Context counting includes rendered source IDs, headings and separators.
Token counting requires `--tokenizer-file`; without it, counts are characters.
Tokenizers are frozen in the comparison directory for resume validation.

## Advanced suites and controlled grids

```bash
ragvi compare-data ./data --reviewed reviewed.json --suite suite.json
```

```json
{
  "schema_version": 1,
  "baseline": "body",
  "policy": "fixed_k",
  "variants": [
    {"name": "body", "technique": "bm25"},
    {"name": "parents", "technique": "parent-child"},
    {"name": "hybrid", "technique": "hybrid", "options": {"lexical_weight": 0.4}}
  ],
  "grids": [
    {"variant": {"name": "chunks", "technique": "bm25"},
     "axes": {"chunk_size": [200, 500], "chunk_overlap": [0, 50]}}
  ],
  "slices": {"versioned": ["identifier"], "multi_fact": ["multiple_sources"]},
  "question_groups": {"Q-reset-1": "reset", "Q-reset-2": "reset"},
  "bootstrap_seed": 42,
  "bootstrap_samples": 2000,
  "warm_repeats": 1,
  "max_configurations": 16,
  "max_query_calls": 4096
}
```

Replace example question IDs/tags with your reviewed data; unknown group IDs fail.
Slices match **all** listed tags. Empty slices report zero questions and N/A rates.
Grid names expand to `chunks-01`, `chunks-02`, etc. Names must be unique and contain
letters, digits, underscores or hyphens. Grid expansion is bounded before execution.

Variant `options` override shared portable defaults for that configuration. Allowed
parameters are k, chunks/overlap, model/provider, base retriever, representation,
child splitter, reranker, stage candidate limits, context budget/tokenizer and hybrid
fusion settings. Input filters, credentials and output paths are shared settings,
not variant options. Relative sidecar/tokenizer paths resolve against the suite file.

A variant can additionally specify `variants_file`, `prefixes_file`, `results_file`
or `usage_file`. Use an `import-data` variant to declare an advanced imported baseline.
For simple `--techniques` requests, `--variants` supplies the multi-query command,
`--prefixes` supplies contextual indexing, and `--reranker-model` supplies rerank.
Use explicit variant options to compose modifiers differently.

Limits: up to 32 expanded configurations (default cap 16), 0–3 additional timing
trials, and 100–10,000 bootstrap resamples. The query-call upper bound includes
original/variant retrieval, hybrid branches, reranking and repeated trials. It
excludes document indexing, model downloads and provider-internal work; it is not a
billing limit. All jobs are planned and bounded before the first retrieval call.

## Dev exploration, freezing and heldout evaluation

Reviewed comparisons default to `--phase dev`. Heldout questions are not retrieved
or scored during that phase. After a dev comparison, `shortlist.json` freezes
successful configurations and their settings. By default it includes all successful
configurations when the baseline succeeds; `--shortlist-names body,hybrid` chooses
a user-selected subset including the baseline. The tool does not optimize selection.

```bash
ragvi compare-data ./data --reviewed reviewed.json --suite suite.json --phase dev --shortlist-names body,hybrid
ragvi compare-data ./data --phase heldout --shortlist ./ragvi-reports/COMPARISON/shortlist.json
```

Keep the shortlist alongside its frozen comparison directory. Corpus, complete
references, configuration and sidecar bindings are validated before heldout use.
Retrieval overrides cannot silently change a frozen shortlist. Explicit `--phase all`
also requires a shortlist for reviewed data. It does not make the data unseen.

Heldout reuse is counted locally under the selected output root, across shortlists
for the same frozen corpus/reference set. The report shows the evaluation number
and prior reuse. This ledger is not global and does not protect against deliberate
edits, deletion or moving to a different output root. Public/reused heldout data
should not be described as an untouched evaluation set.

## Paired uncertainty and timing trials

Intervals are seeded 95% percentile bootstraps over paired question differences.
`question_groups` or unique `family:NAME` tags resample related questions together.
An explicit group overrides that question's tag; group `reset` and tag `family:reset`
share a group. Ungrouped question IDs occupy a separate namespace.
Without declared groups, each question is a unit; authors must assess independence.
All rows within a sampled group stay together, preserving the question-weighted mean.
Repeated runs supply timing observations, not extra independent questions.

Fewer than two declared groups yields an estimate and N/A interval. Small sample
limits are stated. Broad grids involve multiple comparisons; intervals are descriptive
and are not adjusted for choosing a shortlist after exploration.

`--warm-repeats N` records additional trials separately. Vector-cache misses/hits
are labeled `cold_vectors`/`warm_vectors`; model/OS cache warmth remains unknown.
Only compatible vector identities are reused. Timing includes initialization where
measured. Missing query/index timing remains unavailable. Changes in repeated
rankings are flagged; quality summaries and paired intervals use the first trial.

## Optional decision criteria and cost estimates

Suite criteria can name thresholds, not an automatic winner:

```json
{"criteria": {"min_sufficiency_rate": 0.9, "max_mean_query_ms": 150,
              "max_mean_context_units": 1000, "context_unit": "tokens"}}
```

Each split gets matched/not-matched/unknown outcomes with its own measurements.
Unavailable scores/timings and incompatible counter units stay unknown. Scores from
ID-only proxies cannot satisfy actual-context quality thresholds.

Costs remain N/A unless a variant supplies usage and the suite supplies identified
pricing. Usage JSON is an array of unique question/model entries:

```json
[{"question_id":"Q1","model_id":"provider:model","input_tokens":1000,"output_tokens":100}]
```

```json
{"pricing":{"identity":"my-rates-2026-10","currency":"USD","rates":{
  "provider:model":{"input_per_million":0.2,"output_per_million":0.8}}}}
```

These example rates are illustrative. Estimates multiply supplied tokens by supplied
rates; they are not measured provider bills. Missing pricing/model rates or incomplete
question coverage leaves cost unavailable. Usage may include both phases; selected
phase totals are reported. Repeated-trial usage is not inferred or multiplied.

## Failure, resume and private artifacts

```bash
ragvi compare-data . --resume ./ragvi-reports/COMPARISON --format html --format json
```

Resume reads frozen inputs; the INPUT argument is not reread and can be `.`. It
validates input digests, run configuration/context, checkpoints, recomputed span
scores and report facts before reusing completed trials. Modified completed inputs
fail explicitly. Failed/interrupted trials get new attempts; previous artifacts are
kept. Report exports also receive new paths. Resume accepts format/cache/env/browser
controls, not configuration/question changes. Provider endpoint changes require a
fresh comparison; credential rotation does not change the endpoint identity.

Any participant failure produces a partial-failure report and nonzero CLI status.
A failed baseline is not replaced silently. Other completed participants and their
evidence remain visible. No frozen shortlist is created for a failed selected
configuration.

Private files include original snapshots, references, copied sidecars/tokenizers,
suite plans, per-trial runs, frozen search sources and checkpoints. Exports contain
retrieved passages and source locations; inspect them before sharing. HTML has no
remote assets and remains readable without source files or caches. Installed execution
has been verified on Linux; Windows/macOS execution remains a later release gate.
