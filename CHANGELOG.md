# Changelog

All notable user-facing changes are documented here.

## 0.1.0 — 2026-10-08

### Added

- Local BM25 body and heading-context experiments.
- Optional semantic retrieval with FastEmbed, Ollama, and OpenAI-compatible endpoints.
- Import path for existing retrievers.
- Evidence sufficiency, coverage, rank, reciprocal-rank, and precision metrics.
- Question-level regression classification and bounded diagnosis.
- JSON, Markdown, and self-contained HTML reports.
- Guided `ragvidence tutorial` workflow.
- Workspace backup and restore.
- Health and deterministic verification commands.
- Customer documentation, privacy boundaries, and Free/Plus license terms.

### Known limits

- Unanswerable questions are excluded from retrieval-success scoring; abstention is not evaluated.
- The bundled teaching dataset is small, fictional, and English-focused.
- Retrieval evaluation does not establish generated-answer correctness.
