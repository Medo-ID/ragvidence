# RAGvidence

**Diagnose and compare RAG retrieval techniques on your own data.**

RAGvidence helps you decide which retrieval technique to use in your RAG project.
Run experiments on local files, inspect what each technique retrieves, and compare
the evidence without building every experiment yourself. You can also import
results from your own retriever as a baseline.

The CLI is fully free and open source under
[Apache-2.0](https://github.com/Medo-ID/ragvidence/blob/main/LICENSE.md).

## Install

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv tool install --python 3.12 "ragvidence==0.2.1"
ragvi --version
ragvi verify
```

Python **3.12** is required; uv can install it for you. The command is available
from any folder. See the
[installation guide](https://github.com/Medo-ID/ragvidence/blob/main/docs/installation.md)
for upgrades, Windows/macOS/Linux setup, optional PDF/model support and source builds.

## Run on your own data

Ask a question about a file:

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
```

Run several questions against a folder and select your reports:

```bash
ragvi bm25 ./docs --questions ./questions.txt --format html --format json --format markdown
```

The questions file contains one question per nonblank line. Without question
flags, the terminal offers question entry; use `--no-input` for source-only
diagnostics without prompts. Your source files stay unchanged.

The CLI prints a summary and report paths. Open the HTML report in your browser;
it is self-contained and works offline. Reports go under `ragvi-reports/` by
default. Use `--output DIRECTORY` to choose another location.

Supported inputs: UTF-8 TXT and Markdown, visible-text HTML, document JSON/JSONL,
CSV and text-bearing PDF with the `pdf` extra. Folders may mix these formats.
See [input schemas and limits](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-file-usage.md).

## Compare techniques

```bash
ragvi techniques
ragvi compare-data ./docs --questions ./questions.txt --techniques bm25,parent-child
```

Comparisons use the same frozen inputs and questions. Inspect the returned
passages, context size, timings and stage traces. Add reviewed references to
measure whether the retrieved context contains the evidence each question needs:

```bash
ragvi compare-data ./docs --reviewed ./reviewed.json --techniques bm25,parent-child
```

| What you provide | What you learn |
| --- | --- |
| Sources | Extraction, structure and chunk diagnostics |
| Sources and questions | Which passages each technique retrieves |
| Sources and reviewed evidence spans | Evidence sufficiency, coverage, rank metrics, gains and regressions |

Questions alone do not establish relevance. Reviewed references are optional,
but required for scored quality comparisons. Results apply to the data and
questions you tested. RAGvidence helps you choose; it does not change your RAG
system or judge generated answers and citations.

## Choose your next experiment

BM25 runs offline without a model or API key. The catalog also includes dense
search, hybrid RRF, cross-encoder reranking, parent-child retrieval, heading/context
enrichment, multi-query retrieval, metadata filters, MMR, query rewriting and exact
extractive compression. Splitting, overlap, embedding settings and context budgets
can be compared through shared configuration.

- [Getting started](https://github.com/Medo-ID/ragvidence/blob/main/docs/getting-started.md): a complete first experiment and how to read it.
- [Techniques and reviewed evidence](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-techniques.md): requirements, references and your retriever's results.
- [Comparisons and suites](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-comparisons.md): configuration grids, heldout questions, intervals and resume.
- [Advanced techniques](https://github.com/Medo-ID/ragvidence/blob/main/docs/portable-advanced-techniques.md): filters, diversity, rewriting and compression.
- [Coverage and limits](https://github.com/Medo-ID/ragvidence/blob/main/docs/rag-technique-coverage.md): supported experiments and missing techniques.
- [Command reference](https://github.com/Medo-ID/ragvidence/blob/main/docs/command-reference.md): available commands; use `ragvi COMMAND --help` for options.

Want to explore without preparing data? Run `ragvi tutorial` for a small fictional
reviewed comparison and HTML report.

## Models and sharing

Optional FastEmbed embeddings/rerankers run locally after a first model download.
User-owned Ollama models and OpenAI-compatible endpoints are supported for selected
operations. You supply the model/server or API access. See
[provider setup](https://github.com/Medo-ID/ragvidence/blob/main/docs/installation.md#optional-model-support).

Remote endpoints receive the text needed for the operation. Reports can contain
full passages, questions and transformation prompts/outputs. Review them before
sharing. See [privacy and providers](https://github.com/Medo-ID/ragvidence/blob/main/docs/privacy-and-providers.md).

## Contribute and get help

[Report an issue](https://github.com/Medo-ID/ragvidence/issues),
[contribute](https://github.com/Medo-ID/ragvidence/blob/main/CONTRIBUTING.md), improve
the docs or star [the repository](https://github.com/Medo-ID/ragvidence).
For problems, start with [troubleshooting](https://github.com/Medo-ID/ragvidence/blob/main/docs/troubleshooting.md)
and [support](https://github.com/Medo-ID/ragvidence/blob/main/SUPPORT.md).

See [what's new in 0.2.1](https://github.com/Medo-ID/ragvidence/blob/main/CHANGELOG.md),
[security](https://github.com/Medo-ID/ragvidence/blob/main/SECURITY.md) and
[third-party notices](https://github.com/Medo-ID/ragvidence/blob/main/THIRD_PARTY_NOTICES.md).

Copyright © 2026 Medo-ID. Third-party components and models retain their own licenses.
