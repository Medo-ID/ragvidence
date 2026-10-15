# Changelog

All notable user-facing changes are documented here.

## Unreleased

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
