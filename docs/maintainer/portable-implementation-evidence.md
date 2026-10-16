# Portable implementation evidence

Date: 2026-10-16. Scope: M1 integrity foundation, M2 portable BM25 and M3 additional
loaders/configuration plus M4 technique evaluation, M5 comparisons and M6 additional
techniques in development.
M1/M2 were committed as `4479a05`, M3 as `8f7e87c`, M4 as `ff7f06b` (author Medo-ID).
M5 was committed as `173ffc5` (author Medo-ID). M6 implementation evidence follows below.
No package has been published by this work.

## Delivered behavior

```bash
uv run ragvi bm25 docs/examples/device-manual.md --questions docs/examples/questions.txt
uv run ragvi bm25 ./manual.txt --query "Reset instructions" --format html --format json
```

- UTF-8 TXT/Markdown files and recursive folders work without `init` or manually
  prepared workspaces. Internal original-text snapshots and passages are automatic.
- Repeatable query flags, TXT/JSON/JSONL question files, terminal question entry,
  explicit output selection and no-input execution use the same application service.
- Terminal summary and HTML are the default; JSON and Markdown are available.
  Output directories are unique, originals remain unchanged and browsers only open
  when explicitly requested. Report paths are printed without inserted soft wraps.
- Sources-only mode is explicitly `ingestion_only`; supplied questions produce
  `retrieval_inspection`. Neither invents evidence/answer scores. Reviewed evaluation
  remains available through existing workspace commands.
- Original text/line/heading locations and exact returned passages are recorded.
  Actual input preparation settings are retained separately from retrieval settings.
- Questions/output roots, hidden paths, links and generated run directories are
  excluded from source discovery. File/count/byte limits and skipped inputs are explicit.

## M3 loaders and portable configuration

- Offline HTML, document JSON/JSONL and CSV use separate parser adapters feeding
  the same snapshot/chunk/retrieval/report service. Optional pypdf 6.20.1 extracts
  text pages without OCR. Missing extras explain how to install them; no automatic
  dependency installation occurs.
- Source units retain original page, record, JSONL line, CSV row/physical line range
  or HTML section/heading paths, file/text hashes and parser identity. The reports
  show these locations and the exact extracted passages. Physical CSV starts remain
  correct across blank lines and quoted multiline records; newline-ended passages
  do not claim an extra line.
- Only one unambiguous text/content/body field is selected automatically. Other or
  ambiguous schemas require `--text-field`. Metadata stays separate from searchable
  bodies; question/evaluation records and tool artifacts are rejected as documents.
- Include/exclude patterns and file/byte/record/extracted-character budgets are
  configurable. Skipped files, failed extractions and parser warnings are distinct
  in terminal and exports. Global budgets fail rather than silently drop inputs.
- CLI overrides environment, explicit config, user config and defaults, in that
  order. Explicit dotenv values sit below process environment. Config-relative
  paths, missing/invalid settings, list environment values and platform config paths
  have tests. No cwd config/dotenv discovery occurs. Provider secrets are excluded
  from all artifacts, including explicit-env-file runs.
- Old `portable-text-v1` preparation serialization retains its original shape for
  identity validation. New runs identify `portable-files-v1` and record ingestion policy.
- Reviewed fixtures independently specify visible HTML, JSON records, multiline CSV,
  JSONL physical lines and a manually authored three-page PDF with an image-only
  middle page. Real parser tests cover empty, encrypted, malformed and limited PDFs.

## Shared architecture changes

- Canonical JSON preserves meaningful list order and sorts sets before serialization.
  New runs identify schema/hash versions and corpus, questions, references,
  representation, configuration and exact context independently.
- One run validator verifies the dataset binding, question completeness/uniqueness,
  ranks, sources, evidence and exact context before scoring or generating answers.
- Retrieval stages receive source text/IDs without gold evidence labels. Labels are
  reattached from authoritative sources after retrieval; expected answers are not
  exposed to query/retrieval stages.
- Modern evaluation artifacts retain private snapshot/run provenance. Comparison
  and report creation verify their metrics against that provenance. Exported reports
  omit the internal validation snapshot. Legacy evaluations remain explicitly labeled.
- Native/portable execution share configuration resolution, pipeline construction,
  ranking execution, context assembly, artifact storage and report-format dispatch.
- Embedding/cache boundaries reject malformed, nonfinite, zero or nonnumeric vectors;
  provider/endpoint/encoding identity prevents reuse across incompatible providers.
  Imported hit tails are validated before truncation, and missing timing is null.
- Existing tutorial, benchmark, import, evaluate, compare, generate and report
  workflows remain on the shared contracts. The tutorial and release fixtures pass.

## M4 portable technique and evidence path

- One registered CLI callback, options resolver, application service and pipeline
  serve all nine catalog entries. Provider/model overrides, hybrid weights, fusion
  constant, stage-specific candidate limits and whole-passage context selection are explicit.
- Reviewed references bind to frozen original source IDs/hash/quoted character spans.
  Complete interval unions earn one credit per evidence item, independent of chunk
  IDs, overlap, parent expansion or prefix text. Split denominators and unavailable
  unanswerable/answer metrics remain explicit.
- Traces record native branch candidates, timings and scores, nested hybrid/multi-query
  contributions, child mappings, reranker candidates and final budget selection.
  Private `search-sources.json` freezes indexed bodies and supplied prefixes.
- Context budgets count full rendered IDs/headings/separators; exact local tokenizer
  counters disable padding and truncation and record file/package identities.
  Model input truncation is independently disclosed as unmeasured, not conflated
  with returned-context length or proof that all evidence was encoded.
- Exact external spans validate against originals and earn equivalent native scores.
  ID-only imports explicitly score registered-unit proxies. Missing timings remain
  null; all tails are checked before truncation; mixed exact/proxy modes fail.
- Tests include partial/adjacent/gapped/multisource evidence, duplicate overlap,
  changed chunk sizes, budget-induced evidence loss, misleading-prefix regression,
  helpful/noisy query variants, label isolation, source-only execution,
  catalog/prerequisites and export parity. BM25 ties use frozen input order for
  known, OOV and empty-token queries. Optional workspace generation measures full
  system/user message contents; provider framing and billable usage stay unavailable.
- Real offline BGE small, hybrid and Xenova cross-encoder checks pass on a reviewed
  paraphrase with actual local tokenization. [Machine-readable evidence](../../verification/portable-m4/model-check.json)
  records package versions, snapshot revisions and model/tokenizer SHA256 values.
  An additional fixed fictional corpus (eight sources, twelve questions, eleven
  answerable) runs lexical, BGE small, MiniLM, hybrid and reranked configurations
  against identical corpus/reference hashes. Both dense models retrieve the reviewed
  paraphrase; the full per-question outcomes include failures and ties. The evidence
  file records all outcomes rather than asserting a universally superior technique.

## M5 comparison and decision path

- `compare-data` freezes source extraction/questions once. Bounded variants/grids
  rematerialize chunks from originals and call the same snapshot execution service
  as single commands. Existing-system exact-span/ID-proxy baselines participate.
- Declared fixed-k, fixed-token or descriptive policies are checked before model
  calls. Group/slice definitions and supplied usage/pricing have strict schemas.
- Summary facts include sufficiency/coverage/MRR/precision denominators, paired
  evidence gains/losses, split/slice results, observed resources and criterion matches.
  Proxies cannot satisfy actual-context quality thresholds. No automatic winner is declared.
- Seeded paired cluster intervals preserve related question groups. Small/empty
  groups, exploratory grids and repeated timing trials have explicit limits.
- Dev comparisons can freeze user-selected successful shortlists. Heldout execution
  validates their corpus/reference/configuration/sidecar bindings and records local
  reuse, across shortlists for the same frozen evaluation data. Concurrent ledger
  writes reserve unique immutable counters; the ledger is not global/tamper-proof.
- Resume verifies input/checkpoint digests, configuration, original text context,
  recomputed evidence metrics and all derived report facts. It uses frozen inputs,
  retains failures, retries incomplete jobs in new attempts and creates new exports.
- Repeated trials retain separate measurements and observed cold/warm vector states.
  Model/OS cache warmth remains unknown; repeated rankings are checked without
  inflating paired question counts. Runtime package identities accompany native traces.
- JSON/HTML/Markdown consume the same comparison facts. HTML puts changes first,
  keeps ranked context/stages expandable, escapes source text and embeds its font.
- [M5 real-model evidence](../../verification/portable-m5/model-check.json) records a
  four-configuration comparison using BGE/MiniLM, repeated trials and validated
  resume, plus the fixed reviewed quality corpus. Models are fingerprinted; this
  bounded fictional fixture does not prove general production quality.

## M6 additional retrieval techniques

- Typed global/question metadata predicates run before ranking, hybrid branches,
  query variants and child expansion. Missing/type-mismatched fields are excluded;
  empty scopes remain explicit. Resolved predicates are frozen in configurations.
- Cosine MMR uses an explicit embedding adapter/model, bounded candidate pool,
  deterministic ties, incremental redundancy computation, original question and
  preserved input scores/relevance/diversity objectives. It composes after reranking.
- Automatic rewriting/multi-query accepts only the question and configured limit.
  It bounds calls, prompts, query count/length, requested output tokens and timeout;
  strict responses, original-query policy, deduplication, shared RRF and failures
  are recorded. No answers or gold references reach the rewriting provider.
- Deterministic sentence extraction and optional model span selection retain exact
  source-relative offsets. Multiple extracts retain one hit rank; final budgets
  count every rendered extract. Scores use only the surviving original span union,
  and removed qualifications lose evidence credit. Legacy unit scoring rejects
  compression and directs users to portable original-span references.
- Model failures either fail without scoring, retaining private `failure.json`, or
  use an explicit visible original-input fallback. There are no automatic retries.
  Successful prompts/model identities/raw output and selected offsets remain in
  traces. Frozen resume revalidates scopes, transformed queries, compression output,
  MMR objective consistency, exact context, metrics and report facts without model calls.
- Shared candidate retrieval/fusion/reranking, pure selection/predicate/span functions,
  model adapters and CLI option translation keep stages separate from orchestration.
  Existing unused configuration serialization and old suite identities are preserved.
- [Real adapter evidence](../../verification/portable-m6/model-check.json) adds MMR
  after a real cross-encoder with exact tokenizer budgets, reviewed MMR/compression
  runs and a six-configuration repeated comparison with validated resume. Two
  embedding models and the reranker are fingerprinted. Outcomes include failures/ties.
- [Local Qwen evidence](../../verification/portable-m6/transform-check.json) records
  two successful provider/contract checks against the same before/after Ollama digest
  for `qwen3:8b`. Rewriting retained both required items on this one fictional case;
  valid model compression missed both. This is compatible execution, not a quality
  pass or general benchmark. The original 60-second initial timeout remains in
  [the first attempt](../../verification/portable-m6/transform-check-cold.json);
  the digest-pinned retry used explicit 120-second request limits and passed.
- The runnable [M6 example suite](../examples/portable-m6-suite.json) compares lexical,
  version-scoped, diverse and extracted contexts on one dev case plus a separate
  heldout case. Scoped retrieval passes; extraction removes the condition. The
  demonstration's small denominator does not support a general recommendation.

## Current verification

```bash
uv sync --frozen --dev --all-extras
.venv/bin/ruff check src tests scripts
.venv/bin/pytest
.venv/bin/ragvi verify
uv build
.venv/bin/python scripts/check_portable_install.py
git diff --check
```

The test suite contains **358 passing tests** with all extras installed (150 at
M1/M2, 196 at M3, 241 at M4, 274 at M5). The current run is retained in
[the M6 check record](../../verification/portable-m6/checks.json). It includes
cross-process hash-seed checks for dataset identities and saved evaluations;
tampered artifacts; missing/duplicate questions; forged evidence/context; invalid
provider vectors/indexes/caches; input extraction/offsets; question-file exclusion;
explicit failed-run artifacts; source-only behavior; prompt/flag modes; all output
formats; escaped source content; unchanged source files; typed filter truth tables;
independent MMR oracles and helpful/regression cases; rewrite intent drift/output
bounds; exact multi-span compression, qualification loss and budget recovery;
combined stages; frozen heldout filters; and tampered transformation/MMR provenance.

The built wheel was installed into isolated temporary tool/bin directories and
invoked as `ragvi` from an unrelated customer folder. Checks cover spaces and Unicode
in paths, all three exports, source-only execution, HTML/JSON/JSONL/CSV loading,
explicit configuration, reviewed spans, lexical modifier commands, exact external
imports, missing optional PDF support, installation verification,
one-command comparison/resume, dependency-free M6 filters/extraction and the existing tutorial.
CI and release preparation
run this same check, and install
all extras for the parser/tokenizer tests. These runs were on Linux;
they are not evidence of Windows/macOS execution.

## Remaining roadmap work

- M7 optional answer/citation/abstention evaluation and calibrated model judges are
  deferred at the user's request; no M7 capability was added in this milestone.
- Pinned model-revision fingerprints where provider APIs expose them, plus the
  wider model/OS coverage and release gates specified by later milestones.
- Stop before M8: consolidated release verification and publication require a
  scope discussion. Routine milestone checks above do not mark that gate complete.

These remaining features are not claimed by the portable implementation. PDF/
HTML extraction does not establish visual/table/column fidelity; input limits are
not a memory sandbox. Windows/macOS installed execution remains unverified.
