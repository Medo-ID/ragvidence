# Changelog

All notable user-facing changes are documented here.

## 0.2.0 — release candidate (not yet published)

- Adopt Apache-2.0 for the new CLI release, with all included features free and no activation.
- Add shared release gates, platform-matrix installation journeys and capability evidence checks.
- Add typed metadata scopes before ranking, deterministic cosine MMR selection,
  automatic question-only rewriting/multi-query fusion, and exact-span compression.
- Compose the new stages with hybrid retrieval, parents, reranking and context
  budgets; preserve original span evidence, ranking provenance and safe failure traces.
- Bound transformation requests/output, record exact prompts and model/endpoint
  identities, and validate frozen transformations on comparison resume.
- Add `ragvi compare-data INPUT` for one-command technique comparisons over a shared
  frozen corpus, optional existing-system baseline, and HTML/JSON/Markdown decision reports.
- Add bounded configuration grids, declared depth/token/trade-off policies, split/slice
  denominators, paired seeded cluster intervals and per-question evidence gains/losses.
- Freeze dev shortlists before heldout evaluation, record local heldout reuse, and
  validate checkpoints, exact context, recomputed scores and report facts before resume.
- Keep failed attempts visible without overwriting; separate repeat timing trials and
  observed vector cache states. Preserve unavailable timings/costs and label supplied-usage estimates.
- Add portable semantic, hybrid, rerank, parent-child, heading-context, contextual,
  supplied multi-query and existing-system import commands with a capability catalog.
- Score reviewed evidence against complete unions of original text spans; preserve
  labels across chunk changes and expose dev/heldout denominators without answer scores.
- Record stage candidates/scores/timings, nested fusion contributions and exact
  context selection. Add distinct stage limits and whole-passage context budgets
  with exact character or identified local-tokenizer counts.
- Verify external original spans before scoring; label ID-only results as registered-unit
  proxies and retain unavailable timings. Freeze private search sources/prefixes.
- Stabilize BM25 ties in frozen input order, including empty/OOV queries. Measure
  complete message contents in optional workspace generation without inventing provider usage.
- Add offline HTML, document JSON/JSONL and CSV ingestion plus optional `pdf`
  extraction, with page/record/row/heading locations and identified parsers.
- Add explicit text-field selection, document/schema boundaries, input patterns,
  configurable resource limits and separate skipped/failed/warning notices.
- Add portable user/config/environment/CLI precedence and explicit `--env-file`;
  configuration paths resolve relative to their files and credentials stay out of artifacts.
- Add `ragvi bm25 INPUT` for ordinary UTF-8 TXT/Markdown files and folders, with
  question flags/files/prompts, automatic passages and HTML/JSON/Markdown exports.
- Separate unscored questions from reviewed evaluation labels; show explicit
  ingestion-only and retrieval-inspection status without fabricating metrics.
- Fix cross-process dataset hash stability; validate sources, evidence, question
  completeness, ranks and exact context before scoring or generating answers.
- Version new runs, verify modern evaluation artifacts against retained snapshots,
  reject nonfinite scores/vectors, validate complete imports and distinguish missing timing.
- Separate pipeline construction from execution and share atomic artifact storage
  and report-format dispatch across portable and existing workspace commands.
- Include embedding provider/encoding identity in caches and validate cache contents.
- Add an isolated global-style installed-wheel check to CI.

- Add `ragvi experiment WORKSPACE CONFIG_FILE` for reproducible retrieval pipelines.
- Add weighted RRF hybrid BM25/dense search, also available through `benchmark`.
- Add recursive and ATX Markdown child splitting with configurable character overlap,
  parent expansion, child offsets, and deduplication.
- Add multi-query RRF using supplied variants and contextual indexing using reviewed prefixes.
- Add optional local FastEmbed cross-encoder reranking with original stage scores retained.
- Record effective embedding settings, candidate depth, searched queries and returned body character counts.
- Expose full retrieval settings in reports and keep diagnostic explanations appropriate to the intervention.
- Document coverage and missing techniques against the supplied Production RAG resource.

## 0.1.0 — 2026-10-08

### Added

- Local BM25 body and heading-context experiments.
- Optional semantic retrieval with FastEmbed, Ollama, and OpenAI-compatible endpoints.
- Import path for existing retrievers.
- Evidence sufficiency, coverage, rank, reciprocal-rank, and precision metrics.
- Question-level regression classification and bounded diagnosis.
- JSON, Markdown, and self-contained HTML reports.
- Guided `ragvi tutorial` workflow.
- Workspace backup and restore.
- Health and deterministic verification commands.
- Customer documentation, privacy boundaries, and Free/Plus license terms.

### Known limits

- Unanswerable questions are excluded from retrieval-success scoring; abstention is not evaluated.
- The bundled teaching dataset is small, fictional, and English-focused.
- Retrieval evaluation does not establish generated-answer correctness.
