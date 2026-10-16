# Portable techniques and reviewed evidence

These commands are included from version 0.2.0; use a matching release or source build.
The older 0.1.0 release lacks them.
Run them from any directory after installing the development wheel. Use `uv run`
as a prefix when working in the source checkout.

```bash
ragvi techniques
ragvi techniques --format json
ragvi semantic ./data --query "How long do I press the button?"
ragvi hybrid ./data --query "Pairing reset duration"
ragvi rerank ./data --query "Pairing reset duration" --reranker-model Xenova/ms-marco-MiniLM-L-6-v2
ragvi parent-child ./manual.md --query "Reset procedure" --chunk-size 100 --chunk-overlap 10
ragvi heading-context ./manual.md --query "Reset procedure"
ragvi multi-query ./data --questions questions.json --variants variants.json
ragvi contextual ./data --questions questions.json --prefixes prefixes.json
ragvi metadata-filter ./records.json --query "Reset procedure" --filters filters.json
ragvi mmr ./data --query "Reset procedure" --mmr-lambda 0.3
ragvi auto-multi-query ./data --query "Reset procedure" --rewrite-model qwen3:8b
ragvi compress ./data --query "Reset procedure"
```

All techniques use the same ingestion, snapshot, context assembly and report
exports described in [Portable file usage](portable-file-usage.md). Without reviewed
references they provide inspection, not quality scores or a recommended winner.

BM25, semantic and hybrid are base retrievers. Modifier commands use BM25 by default;
`--base-retriever semantic` or `hybrid` changes that base. Optional `--representation`
accepts `body`, `heading_context` or `contextual`. `--reranker-model` can also add a
cross-encoder to another native command. `--model`/`--provider` select dense settings.
`--lexical-weight` sets the hybrid lexical share (strictly between zero and one);
`--rrf-constant` sets the fusion constant.
`heading-context` requires authentic headings; it fails on wholly flat input.

Local embeddings and cross-encoders require `ragvidence[semantic]`. The CLI discloses
first-use model downloads. `--cache-dir` controls vector caches and the `models/`
subdirectory used by both local adapters. Remote providers receive source text and
search queries; the CLI discloses this before execution. Keys remain in environment
settings, outside reports.

The parent-child command searches small children and returns full original source
units: one TXT/Markdown document, HTML section, structured record or PDF page. Other
commands return independent passages. Character overlap stays within a Markdown
section. A full parent may recover evidence absent from the matching child, at the
cost of more returned text. Neither full parents nor model truncation guarantee that
every character influenced a model's ranking.

## Reviewed span references

First inspect sources without questions:

```bash
ragvi bm25 ./manual.txt --no-input --format html --format json
```

The source inventory contains original IDs, text hashes, extracted locations and
the corpus hash. The private `snapshot.json` contains the exact extracted bodies
used for character offsets. Make a reviewed JSON sidecar with this structure:

```json
{
  "schema_version": 1,
  "corpus_hash": "COPY_FROM_SOURCE_REPORT",
  "evidence": [
    {"evidence_id": "RESET", "spans": [
      {"source_id": "COPY_ORIGINAL_SOURCE_ID", "start": 0, "end": 13, "text": "eight seconds"}
    ]}
  ],
  "questions": [
    {"question_id": "Q1", "question": "How long is reset?", "split": "dev",
     "answerable": true, "required_evidence_ids": ["RESET"]}
  ]
}
```

The offsets above only apply if the original body begins with `eight seconds`.
Offsets are zero-based Unicode characters with an exclusive end, relative to the
original extracted source unit. Every quote, source and corpus hash is validated.
One evidence item may require multiple spans, including spans in different sources.
Question splits are `dev`/`heldout`; tags and reference answers are optional. Answers
remain evaluation data and are never sent into retrieval stages.

```bash
ragvi bm25 ./manual.txt --reviewed reviewed.json
ragvi parent-child ./manual.txt --reviewed reviewed.json --chunk-size 100
```

`--reviewed` supplies questions and cannot combine with `--query`/`--questions`.
The state becomes `reviewed_evaluation`. Full union coverage of every required span
earns evidence credit, even across several chunks; partial coverage and duplicate
overlap cannot inflate that credit. Changing chunk size/overlap preserves the
original corpus identity and reviewed references. Prefixes never earn span credit.

Reports record sufficiency, fraction of complete required evidence, first prefix
rank completing any required item, reciprocal rank and overlap precision divided
by configured k. Dev/heldout summaries keep answerable denominators separate.
Unanswerable questions have N/A retrieval metrics; answer correctness, citations
and abstention are not scored. `evaluation.json` stores the same computed facts.
The existing optional workspace generation command also measures complete system/user
message contents with the identified counter; provider framing/billable usage remain
unavailable. Portable commands do not generate answers.

The checkout includes a complete example:

```bash
ragvi hybrid docs/examples/device-manual.md --reviewed docs/examples/portable-reviewed.json
ragvi multi-query docs/examples/device-manual.md --reviewed docs/examples/portable-reviewed.json --variants docs/examples/portable-variants.json
```

## Explicit stages and context budgets

| Option | Meaning |
| --- | --- |
| `--branch-k` | Maximum candidates from each lexical/dense hybrid branch |
| `--child-k` | Maximum children before parent deduplication |
| `--query-k` | Maximum returned candidates for each original/variant query and its fused pool |
| `--rerank-k` | Maximum retrieved candidates scored by the cross-encoder |
| `--k` | Maximum final returned source units |
| `--context-budget` | Maximum complete rendered context count |
| `--tokenizer-file` | Local Hugging Face tokenizer JSON; count tokens instead of characters |

Explicit stage limits are caps: a small pool can return fewer than k results. Legacy
workspace `candidate_k` remains supported as the fallback shared candidate limit.
Without explicit stage limits, extended pipelines use at least 20 candidates and
simple BM25/dense pipelines use k. Specify `--query-k` to bound a broader candidate
pool when exploring a context budget.

Budget selection preserves ranked whole passages, skips those that do not fit and
renumbers the selected results. It counts IDs, headings and separators in the
rendered retrieval context. The default counter is exact Unicode characters. An
explicit tokenizer is hashed and identified, with padding/truncation/special tokens
disabled for counting the complete text. Token counts are exact for that supplied
tokenizer; they exclude generation instructions and model request overhead.

No text is silently cut to fit a budget. Removed passages lose evidence credit.
Model adapters may independently truncate embedding or reranker inputs; exact
per-model truncation counts are currently unavailable and disclosed in reports.

JSON/HTML/Markdown reports expose stage candidates, scores, timings, searched query
strings and budget selection. Nested fusion retains underlying branch contributions.
`run.json` records the exact final context; `search-sources.json` freezes the search
bodies and reviewed prefixes. These private artifacts may contain substantial corpus
text. Inspect exports and working artifacts before sharing.

## Variants and prefixes

Variant JSON maps question IDs to one through eight supplied nonblank strings:

```json
{"Q1": ["pairing reset duration", "hold reset button"]}
```

The original question is always searched. Duplicate strings are removed; unknown
question IDs fail. Prepare supplied variants independently of expected evidence,
particularly for heldout questions. Separate `rewrite` and `auto-multi-query`
commands generate variants through an explicit question-only model interface.

Prefix JSON maps every original source ID to a reviewed prefix and text hash:

```json
{"COPY_ORIGINAL_SOURCE_ID": {"text_hash": "COPY_ORIGINAL_TEXT_HASH", "prefix": "Device documentation"}}
```

Every source must match. Prefixes are inherited by that source's passages; original
bodies remain unchanged. Misleading prefixes and noisy variants can cause regressions.

## Existing-system results

```bash
ragvi import-data ./data --reviewed reviewed.json --results results.jsonl
```

Use one JSONL record per supplied question, including questions with empty hits:

```json
{"question_id":"Q1","hits":[{"source_id":"COPY_ORIGINAL_SOURCE_ID","start":0,"end":13,"text":"eight seconds","rank":1,"score":0.8}]}
```

Exact imports must match original text and offsets. Native and imported equivalent
spans earn identical evidence credit. For ID-only results, use `source_unit_id`
instead of the span fields, referencing a registered original or passage from the
snapshot. Such scores are explicitly `registered_unit_proxy`; actual external
context was not supplied. Exact and proxy hits cannot mix in one run. All hit tails
are validated before selection. Missing query/index timings remain unavailable.
External internal-stage traces and generation-request context are unavailable.

One-command comparisons, paired intervals, controlled grids and resumable suites
are available through [compare-data](portable-comparisons.md). Typed metadata filters,
MMR, automatic rewriting and extractive compression are covered in the
[advanced technique guide](portable-advanced-techniques.md), including composition,
provider/output bounds, failure provenance and exact-span evidence rules.
Current real-model evidence covers a paraphrase smoke fixture and a
fixed fictional corpus (eight sources, twelve questions) with two embedding models,
hybrid and reranking. Results include failures and ties. These bounded fixtures do
not prove general quality or that an alternative improves a user's RAG.
