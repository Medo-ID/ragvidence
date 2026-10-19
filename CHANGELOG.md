# Changelog

## 0.2.1 (unreleased)

- Unify inspection, technique comparison and workspace HTML reports in a compact
  CLI-style grid with embedded Geist typography, jump navigation and labeled outcomes.
  Default to a neutral dark theme with an optional embedded light/dark toggle.
- Surface execution failures, unavailable measurements and resource trade-offs;
  keep configuration, hashes and stage JSON in keyboard-accessible disclosures.
- Improve narrow-screen tables, long paths, source passages and paper/PDF output,
  including evidence inside closed disclosures. Reports remain self-contained and
  useful offline with JavaScript disabled. Retrieval, scoring and schemas are unchanged.

## 0.2.0

RAGvidence is a fully free, open-source CLI under Apache-2.0. This update brings
retrieval experiments and evidence reports directly to your own files and folders.

### Use your data without project setup

- Run `ragvi TECHNIQUE INPUT` from any folder. Use TXT, Markdown, visible-text HTML,
  document JSON/JSONL, CSV or text-bearing PDF with the `pdf` extra.
- Supply questions with flags, files or the terminal prompt. Inspect sources
  without questions using `--no-input`.
- Get a terminal summary and self-contained HTML, JSON or Markdown reports with
  source locations, settings, warnings and exact returned context.

### Explore and compare retrieval techniques

- Use BM25, dense search, weighted hybrid RRF, cross-encoder reranking,
  parent-child retrieval, heading/context enrichment and multi-query fusion.
- Test typed metadata filters, cosine MMR, bounded model query rewriting and
  exact extractive compression. Configure splitting, overlap and context budgets.
- Import your retriever's results as a comparison baseline, with original-span
  validation or explicitly limited source-ID proxies.
- Compare configurations on one frozen corpus with `ragvi compare-data`. Use
  bounded grids, separate dev/heldout questions, paired intervals and validated
  resume. Inspect per-question gains, regressions and failed attempts.

### Evaluate evidence and preserve reproducibility

- Score reviewed original evidence spans after context selection and compression.
  Report sufficiency, coverage, rank and precision with explicit denominators.
- Keep unreviewed retrieval inspection separate from scored evaluation. Generated
  answers and citations are not judged.
- Retain input hashes, source offsets, stage rankings, model/provider settings,
  transformation traces and cache identity. Keep missing timings/costs explicit.
- Validate artifacts, imports and resumed comparisons before using their results.

### Installation and reliability

- Support Python 3.12 with automated installed-package checks on Linux x64,
  Windows x64 and macOS Apple Silicon/Intel.
- Exercise isolated wheel/source installations, optional runtimes and upgrades.
  Keep Windows JSON/version output clean and preserve CRLF source offsets.
- Include a capability catalog, bundled verification, input examples, contribution
  guidance and issue/PR templates.
