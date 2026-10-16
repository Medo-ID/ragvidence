# Filters, diversity, rewriting and extractive compression

These M6 capabilities are implemented in the development build. They diagnose
trade-offs on your data; they do not change your RAG system. Use reviewed original
spans for quality scores, or questions alone for unscored inspection.

```bash
ragvi metadata-filter ./records.json --query "Reset procedure" --filters filters.json
ragvi mmr ./docs --query "Reset procedure" --mmr-lambda 0.3 --mmr-candidates 30
ragvi rewrite ./docs --query "Reset procedure" --rewrite-model qwen3:8b
ragvi auto-multi-query ./docs --query "Reset procedure" --rewrite-model qwen3:8b --rewrite-count 3
ragvi compress ./docs --query "Reset procedure" --compression-max-spans 2
```

All commands accept the existing file loaders, questions, reviewed references,
context budgets, report formats, output and cache flags. Modifier commands default
to BM25; `--base-retriever semantic` or `hybrid` changes their first retriever.
`ragvi techniques` lists prerequisites. Deterministic filters and sentence extraction
need no model. Local MMR needs `ragvidence[semantic]` or a configured remote embedding
provider. Automatic rewriting and model span selection use your explicit provider.

## Typed metadata filtering

`filters.json` contains global predicates and optional question-specific predicates:

```json
{
  "all": [
    {"field": "record_metadata.product", "op": "in", "value": ["DeskHub", "Dock"]},
    {"field": "record_metadata.version", "op": "gte", "value": 2}
  ],
  "questions": {
    "Q1": [{"field": "source_path", "op": "eq", "value": "manual.json"}]
  }
}
```

Fields address source metadata through dot-separated object keys. JSON/JSONL fields
other than the document text live under `record_metadata`; CSV columns also live
there and retain string values. Built-in metadata includes `source_path`, `format`,
`loader` and `location.page`/`location.record` where applicable. No document metadata
is inferred from prose. Literal keys containing dots are not addressable.

All global and matching question predicates are combined with AND. Supported
operators are `eq`, `in`, `gt`, `gte`, `lt`, `lte`. Equality/membership distinguish
strings, booleans, numbers and null; integers/floats share the numeric type. Missing
fields and type mismatches exclude the source. Explicit null can match `eq: null`;
a missing field cannot. Range operators compare numbers or strings of the same
kind. String order is lexical, including dates/version strings; no date, numeric
string or semantic-version conversion occurs. Arrays/objects are not scalar values.

The limit is 32 global and 32 predicates per question, and 100 values per `in`.
Unknown question IDs fail. Suites validate against all reviewed IDs, then select
only the current phase's filters. A scope with zero matches returns an explicit
empty result without ranking. The trace records predicates and eligible IDs.

Filtering happens before ranking, hybrid branches, supplied/generated variants
and child creation. Parent expansion cannot reintroduce excluded sources.
Identical scopes share an index within a run; total index time includes their
preparation. MMR indexes only the union of eligible source units.

## Maximum marginal relevance (MMR)

MMR selects from the retrieved pool using:

```text
lambda * cosine(original question, candidate)
  - (1 - lambda) * maximum cosine(candidate, already selected candidates)
```

The first candidate has zero redundancy penalty. Ties preserve incoming candidate
order. At lambda 1, selection follows query cosine relevance; at lambda 0, the first
candidate is the first incoming candidate and subsequent choices minimize maximum
similarity to the selected set. Scores can be negative and are not probabilities.

`--mmr-candidates` caps the input pool (default 20, maximum 1000). The entire pool
is ordered by MMR before final depth/budget selection. `--query-k`, branch/child
limits and `--rerank-k` can restrict the available pool first. Explicit limits are
never expanded to satisfy MMR. Returned depth can be less than k.

MMR follows optional cross-encoder reranking and uses the original question's
embedding. Its relevance objective is cosine, even when the incoming candidates
were ranked lexically or by a cross-encoder. `--model` and `--provider` explicitly
identify these embeddings; resolved settings, adapter identity, prior scores,
relevance, redundancy, objective and measured selection time are recorded.
Compatible document vectors are cached through the existing embedding service.

Diversification can recover complementary facts or displace required similar
passages. Compare the actual final evidence. A larger or more diverse pool is
not evidence of better retrieval quality.

## Automatic question rewriting and query variants

Set `RAGVIDENCE_TRANSFORM_BASE_URL` for your service. Ollama defaults to
`http://localhost:11434`; OpenAI-compatible services require an explicit base URL.
`RAGVIDENCE_TRANSFORM_API_KEY` supplies an optional credential. These settings are
separate from embedding and optional answer-generation providers.

```bash
ragvi rewrite ./docs --questions questions.json --rewrite-model qwen3:8b --rewrite-only
ragvi auto-multi-query ./docs --questions questions.json --rewrite-model my-model --rewrite-provider openai_compatible --rewrite-count 3
```

`rewrite` requests one query. `auto-multi-query` requests up to three by default,
configurable from one to eight. The provider receives only the original question
and the limit, plus a versioned instruction; no source bodies, reference answers,
evidence IDs or reviewed labels are supplied to rewriting.

The original question participates by default. `--rewrite-only` stops automatic
insertion of the original; a model can still return the same text. Queries are
trimmed and deduplicated. Supplied `--variants` may also participate. All query
rankings use the same scope and existing RRF implementation. Final evaluation,
cross-encoder reranking and MMR continue to use the original question.

Strict JSON output is required: `{"queries": ["query text"]}`. Blank queries,
extra keys, duplicate JSON keys, over-limit responses and malformed output fail.
`--rewrite-failure original` explicitly falls back to the original question; the
default is `fail`. A fallback is visible in the terminal/report and never relabeled
as successful rewriting. There are no automatic retries or self-correction loops.

## Extractive compression

The default `sentences` selector splits each candidate at punctuation/newline
boundaries, ranks spans by the number of distinct question words they share, and
keeps up to two positive-overlap spans per source. Ties use original offset order.
Selected spans return in source order, within the incoming source ranking.
There is no stemming, semantic matching or language-specific sentence parser.
No lexical overlap means no selected spans for that source.

An optional model selector receives the original question and candidate bodies:

```bash
ragvi compress ./docs --questions questions.json --compression-model qwen3:8b
ragvi parent-child ./docs --query "Reset procedure" --compressor sentences --context-budget 2000
```

The model must return exact Unicode character offsets, never rewritten text:

```json
{"selections": [{"source_unit_id": "COPY_CANDIDATE_ID", "start": 0, "end": 34}]}
```

IDs must come from the candidate pool. Offsets are relative to that candidate's
body, including a full parent after expansion. Bounds, strict integer types,
ordering, overlap and the per-source limit are validated. An empty selection is
valid. `--compression-max-spans` permits 1–16 spans per source. Each extract retains
its exact mapping into the original extracted source. No added summary text earns
evidence credit. The model can still select unhelpful or incomplete valid spans.

Final context budgets count all extracts, IDs, headings and separators. Whole
compressed source groups are kept or skipped; spans are not silently shortened.
Several extracts from one source keep one retrieval rank and count as one hit for
precision/depth. Reports display each extract with that rank and exact location.
Evidence is recomputed from the returned span union, so removed conditions or
qualifications lose credit. Legacy workspace unit labels cannot establish that
compressed text contains a fact: use portable original-span evaluation instead.

`--compression-failure original` explicitly permits unchanged candidates on invalid
model output/provider failure; default `fail` produces no scored result. Extractive
compression does not implement abstractive summaries, answer generation or judging.

## Combinations, bounds and frozen evidence

Single commands can combine stages through flags or nested portable JSON/TOML
options. In a suite, each variant's `options` accepts `filters`, `mmr`, `rewrite`
and `compression`. Example fragment:

```json
{
  "name": "scoped-diverse-extracts",
  "technique": "hybrid",
  "filters_file": "filters.json",
  "options": {
    "mmr": {"lambda_mult": 0.3, "candidates": 30},
    "rewrite": {"model": "qwen3:8b", "count": 3, "timeout_seconds": 120},
    "compression": {"mode": "sentences", "max_spans": 2}
  }
}
```

`filters_file` is resolved relative to the suite and excluded from corpus discovery;
its parsed contents are frozen into the run configuration. Model stages also accept
`provider`, `failure`, `timeout_seconds` (1–300; default 60) and
`max_output_tokens` (32–4096; defaults 512 rewrite, 1024 compression). Ollama requests
disable thinking and request temperature zero; compatible services receive a token
cap. Provider enforcement and billable usage are not independently measured.

Every model prompt is limited to 100,000 characters; returned JSON is limited to
16,000 characters, and each rewritten query to 8,000 characters. Suite call bounds
include generated-query upper limits, rewriting, MMR query encoding and optional
model compression. Exceeding the suite budget fails before any model execution.

```bash
ragvi compare-data ./docs --query "Reset procedure" --techniques bm25,mmr,compress
ragvi compare-data ./docs --reviewed reviewed.json --suite suite.json
```

A complete fictional example (MMR requires the semantic extra or an embedding
provider) is included in the source archive:

```bash
ragvi compare-data docs/examples/portable-m6-records.json --reviewed docs/examples/portable-m6-reviewed.json --suite docs/examples/portable-m6-suite.json
```

It has one dev case and a separate heldout case; small-sample intervals remain N/A.
Scoped retrieval keeps the correct version, while extraction drops a required
condition. It is a worked diagnostic example, not a quality benchmark.

For simple `--techniques` comparisons, stage-specific flags configure the matching
technique entry; the BM25 baseline stays plain. To apply shared filters/modifiers
or test combinations, declare them explicitly per variant in a suite. See
[comparisons](portable-comparisons.md) for frozen dev shortlists and heldout use.

Stage evidence records actual queries, prompts, model/provider/endpoint identity,
bounded raw outputs, input candidates and selected offsets. Query rewriting and
model compression retain no references or gold answers in their prompts. Resuming
valid completed trials uses their recorded outputs and does not call a model again.
Invalid default-fail transformations retain private `failure.json` evidence and
produce no scored report for that trial. Do not share prompt/source artifacts
without reviewing their contents.

Model names/endpoints can resolve to changed weights. Runs record configuration
and adapter identities, but do not independently pin every runtime model revision.
The local model compatibility check records/checks its Ollama content digest;
the cached-model check fingerprints its own model files. Those checks do not make
an arbitrary future user run immutable. Broader revision pinning remains release work.

The M6 checks include independent ranking/predicate/span oracles, positive and
regression cases, composition tests, installed CLI journeys, real cached embedding
and reranker checks, and bounded local Ollama compatibility checks with recorded
model digest. These establish supported behavior, not universal quality. M7 answer
evaluation is deferred; consolidated M8 release verification has not started.
