# RAGvidence

**Diagnose and compare RAG retrieval techniques on your own data.**

Install `ragvi` once and run it from any data folder. Inspect the technique you
already use, import your system’s retrieved results, and compare alternatives
without implementing every experiment. RAGvidence produces evidence to help you
choose a technique for your project. It does not change your production RAG system.

This documentation covers **0.2.0**, a free CLI under [Apache-2.0](https://github.com/Medo-ID/ragvidence/blob/main/LICENSE.md).
All included capabilities are available without an account or activation.
Voluntary sponsorship does not unlock features. The earlier published 0.1.0 has
its original license and lacks the portable commands described here; check
`ragvi --version` and use the matching release documentation.

## Install

Python **3.12** is required. Install the matching version from PyPI:

```bash
uv tool install --python 3.12 "ragvidence==0.2.0"
ragvi --version
ragvi verify
```

Optional runtimes are installed as `"ragvidence[pdf,semantic]==0.2.0"`.
If that version is not yet available on the index, build this source and install
the exact wheel:

```bash
uv build --out-dir dist/release
uv tool install --python 3.12 ./dist/release/ragvidence-0.2.0-py3-none-any.whl
```

The [release checks](https://github.com/Medo-ID/ragvidence/actions/runs/38921470479)
passed on Linux x64, Windows x64, macOS Apple Silicon and macOS Intel: 395 tests
per platform plus installed-package and 0.1.0 upgrade journeys. Other Python versions,
architectures and model/hardware combinations are not covered by those checks.

After 0.2.0 is available, existing uv-tool installations can upgrade with
`uv tool upgrade ragvidence`. Check `ragvi --version` afterward. Preserve old
workspaces: legacy artifacts remain readable, but rerun experiments when modern
span/hash validation is needed.

## Use your own data

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
ragvi bm25 ./docs --questions ./questions.txt --format html --format json
ragvi compare-data ./docs --questions ./questions.txt --techniques bm25,parent-child
ragvi techniques
```

No workspace or project setup is needed. The command prints a summary and writes
self-contained HTML by default under `ragvi-reports/`. Repeat `--format` to choose
HTML, JSON and/or Markdown; `--output` selects the destination.

Inputs: UTF-8 TXT and Markdown, visible-text HTML, document JSON/JSONL, CSV and,
with the `pdf` extra, text-bearing PDF pages. Folders may mix these formats.
Scans/OCR, DOCX, spreadsheets, images, URL crawling and database connectors are
not included. Extraction does not establish table or page-layout fidelity.

| Input | Result |
| --- | --- |
| Sources only | Extraction/chunk diagnostics; no retrieval-quality score |
| Sources and questions | Ranked passages, traces, timings and context inspection |
| Sources and reviewed original-span evidence | Evidence sufficiency, coverage, rank, reciprocal rank, precision and paired comparisons |

A document alone cannot tell the tool which evidence a question requires.
Reviewed references are optional but necessary for scored quality claims.
Answer correctness, citation correctness and abstention judging are not included.

## Techniques

The catalog includes BM25, dense cosine, weighted hybrid RRF, cross-encoder
reranking, parent-child retrieval, heading context, supplied reviewed context
prefixes, supplied multi-query fusion, typed metadata filters, MMR, automatic
query rewriting/multi-query generation, exact extractive compression and existing
system imports. Recursive/Markdown splitting, overlap, context budgets and
embedding configuration comparisons are composed through shared configuration.
A catalog entry is a runnable preset or import path, not a claim of an independent
algorithm or guaranteed improvement.

Comparisons share frozen data and references, record per-question gains and losses,
retain failures, support bounded grids, dev shortlists, heldout evaluation,
paired intervals and validated resume. Small or unrepresentative datasets cannot
establish a general winner. Missing costs/timings remain unavailable.

- [Portable files and formats](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-file-usage.md)
- [Techniques, reviewed evidence and external imports](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-techniques.md)
- [Comparisons and experiment suites](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-comparisons.md)
- [Filters, MMR, rewriting and compression](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-advanced-techniques.md)
- [Coverage and remaining gaps](https://github.com/Medo-ID/ragvidence/blob/main/docs/rag-technique-coverage.md)
- [Command reference](https://github.com/Medo-ID/ragvidence/blob/main/docs/command-reference.md)

## Local models and data boundaries

BM25 needs no LLM or network. Optional FastEmbed embeddings and cross-encoder
reranking download selected model files before local inference. Ollama supports
user-owned embedding models and chat models for query rewriting or model-selected
exact-span compression. OpenAI-compatible endpoints are also supported; the user
chooses whether an endpoint is local or remote. Sentence compression needs no model.

There is no bundled LLM server, API credit, GPU requirement guarantee or promise
that every model follows the output contracts. Review each model’s license and
hardware needs. Model tags may change; compatibility checks for specific pinned
files/digests do not pin every user run. Remote endpoints receive the text needed
for the selected operation. Reviewed answer labels are kept out of retrieval
and transformation prompts.

Credentials are excluded from manifests. Reports and frozen artifacts can contain
full source passages, questions and transformation prompts/outputs: review them
before sharing. HTML uses escaped content, embedded fonts and no remote assets.
Third-party providers and model download services have their own data policies.

## Existing workspace workflow

`ragvi tutorial` creates a bundled fictional comparison and HTML report.
The earlier `benchmark`, `import-run`, `evaluate`, `compare`, `report` and recovery
commands remain available. Optional `generate` produces answers for inspection;
it does not score their correctness. See [getting started](https://github.com/Medo-ID/ragvidence/blob/main/docs/getting-started.md).

## Contribute and support

RAGvidence is open source. [Report a reproducible problem](https://github.com/Medo-ID/ragvidence/issues),
[contribute a change](https://github.com/Medo-ID/ragvidence/blob/main/CONTRIBUTING.md), improve the docs, share the project, or star
[the repository](https://github.com/Medo-ID/ragvidence) if it helps you.
See [support](https://github.com/Medo-ID/ragvidence/blob/main/SUPPORT.md) for what to include in a report.

Financial sponsorship is not configured yet. When available it will be optional,
with no features or support guarantees tied to payment. All included CLI features
remain free. The separate website will be updated in a later session.

## Verify a release candidate

```bash
uv sync --frozen --dev --all-extras
uv run --no-sync python -m scripts.verify_release --online-install
```

This shared gate runs offline unit/contracts, fixture verification, distribution
inspection, and isolated core wheel, source and optional-runtime installation
journeys from unrelated folders. GitHub Actions repeats it across the CI matrix;
fresh package installations may fetch locked dependency metadata from PyPI.
Real model compatibility checks and manual CLI/report usability are separate.
See [security](https://github.com/Medo-ID/ragvidence/blob/main/SECURITY.md), [support](https://github.com/Medo-ID/ragvidence/blob/main/SUPPORT.md), [changelog](https://github.com/Medo-ID/ragvidence/blob/main/CHANGELOG.md),
[third-party notices](https://github.com/Medo-ID/ragvidence/blob/main/THIRD_PARTY_NOTICES.md) and [dependency licenses](https://github.com/Medo-ID/ragvidence/blob/main/THIRD_PARTY_LICENSES.md).

Copyright © 2026 Medo-ID. New releases from 0.2.0 use Apache-2.0;
third-party components and models retain their own licenses.
