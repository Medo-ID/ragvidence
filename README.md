# RAGvidence

**Evidence-first RAG diagnostics, built to run locally.**

RAGvidence is a local, CLI-first toolkit for testing retrieval changes with reviewed evidence instead of judging generated answers by intuition.

It helps you answer questions such as:

- Did the retriever return **all** evidence required for the answer?
- Did a new chunk representation fix failures or introduce regressions?
- Is the first relevant result early enough at the real context depth `k`?
- Does lexical, semantic, or an existing application retriever work better on your data?

No account, telemetry, hosted database, or vendor-provided API key is required. BM25 works completely offline. Semantic retrieval can run locally or through a provider chosen by the user.

> RAGvidence evaluates retrieval evidence. It does not prove that a generated answer is correct, safe, or legally compliant.

## Install

### Production PyPI

```bash
uv tool install --python 3.12 "ragvidence[semantic]"
ragvi health
ragvi tutorial
```

See the [public installation guide](https://ragvidence.medo-id.com/docs/installation).
The report presentation in the development source build is documented separately
from the currently published PyPI release; publishing it requires a new release.


### Customer release archive

Extract the release, open a terminal in its directory, and run:

```bash
uv sync --frozen
uv run ragvi health
uv run ragvi tutorial
```

During source-based use, prefix commands with `uv run`. After installing the CLI as a tool, use `ragvi` directly.

### Install a built wheel

```bash
uv tool install ./ragvidence-0.1.0-py3-none-any.whl
ragvi health
ragvi tutorial
```

Python 3.12 is pinned in `.python-version`; `uv` can install the required Python runtime automatically.

## First report

The development source also includes the first portable file/folder command:

```bash
uv run ragvi bm25 ./manual.txt --query "How do I reset the device?"
uv run ragvi bm25 ./docs --questions ./questions.txt --format html --format json
```

It reads TXT, Markdown, HTML, document JSON/JSONL and CSV (text PDFs with the optional
`pdf` extra), prepares passages automatically, prints retrieved results,
and writes reports under `ragvi-reports/`. No workspace setup is needed. Without
questions it produces source diagnostics; `--reviewed` adds validated original-span
evidence scoring. Semantic, hybrid, reranking, parent-child, contextual and supplied
multi-query commands share this workflow; `ragvi techniques` lists prerequisites.
After installing a wheel built from this source,
invoke `ragvi` directly from any directory. See [Portable file usage](docs/portable-file-usage.md).
This command is not yet part of the published PyPI release.
See [Portable techniques and reviewed evidence](docs/portable-techniques.md) for
technique settings, context budgets and existing-system imports.

The tutorial writes a complete comparison to:

```text
workspaces/first-run/reports/tutorial.html
```

Open it in any browser. It contains the baseline, intervention, changed questions, diagnosis, ranked evidence, limitations, and reproducibility metadata.

Then follow [Getting started](https://ragvidence.medo-id.com/docs/first-tutorial) to understand the experiment rather than only running it.

## Supported workflows

| Goal | Start here |
| --- | --- |
| Learn the workflow on bundled data | `ragvi tutorial` |
| Evaluate your own labeled dataset | [Bring your own data](https://ragvidence.medo-id.com/docs/bring-your-own-data) |
| Compare BM25 and semantic retrieval | [User guide](https://ragvidence.medo-id.com/docs/semantic-workflow) |
| Test an existing RAG retriever | [User guide](https://ragvidence.medo-id.com/docs/import-retriever) |
| Generate optional answers for inspection | [User guide](https://ragvidence.medo-id.com/docs/commands) |
| Understand each metric | [Interpreting results](https://ragvidence.medo-id.com/docs/metrics) |
| Recover a broken workspace | [Troubleshooting](https://ragvidence.medo-id.com/docs/troubleshooting) |
| Review data and provider boundaries | [Privacy and providers](https://ragvidence.medo-id.com/docs/privacy-providers) |

The complete CLI reference is in [Command reference](https://ragvidence.medo-id.com/docs/commands).

## What is included

The development source build also supports JSON-configured hybrid RRF search,
parent-child retrieval with recursive or Markdown splitting and overlap,
supplied query variants and contextual prefixes, and optional local cross-encoder
reranking. See [technique coverage, examples, and remaining gaps](docs/rag-technique-coverage.md).
These additions are not yet published to PyPI.

- Controlled body versus heading-context experiments
- BM25 lexical retrieval
- Optional local semantic retrieval with FastEmbed
- Ollama and OpenAI-compatible embedding adapters
- Import of ranked results from another RAG stack
- Evidence sufficiency, coverage, first relevant rank, reciprocal rank, and precision@k
- Explicit improvement and regression classification
- Evidence-backed diagnostic suggestions
- JSON, Markdown, and self-contained HTML reports
- Optional answer inspection using a user-selected model
- Recoverable local workspaces and deterministic installation verification

## Free and Plus

The current release contains the complete Free feature set. Plus is a separate paid entitlement for advanced features released in Plus builds; features are never advertised as available until they ship. See [Plans and editions](https://ragvidence.medo-id.com/#plans) and [LICENSE.md](https://ragvidence.medo-id.com/ragvidence-0.1.0-license.txt).

The Free edition does not require activation. Plus activation will be issued after verified checkout and must never require placing payment credentials inside this CLI.

## Privacy and trust boundaries

- Workspaces, caches, `.env`, and generated reports are ignored by Git.
- BM25 performs no network requests.
- FastEmbed downloads a model, then performs inference locally.
- Remote providers receive source text and questions; the CLI displays a disclosure first.
- API keys are loaded from `.env` and are not included in run manifests or reports.
- HTML reports escape dataset content, contain no scripts, and use no remote assets.
- Reports include short source previews and may still contain confidential information. Review before sharing.

## Development and release verification

```bash
uv sync --frozen --dev
uv run ruff check src tests
uv run pytest
uv run ragvi verify
uv build
```

See [Security](https://ragvidence.medo-id.com/security), [Support](https://ragvidence.medo-id.com/docs/troubleshooting), [Changelog](https://ragvidence.medo-id.com/releases), [Third-party notices](https://ragvidence.medo-id.com/ragvidence-source-notices.txt), and the [resolved dependency inventory](https://ragvidence.medo-id.com/ragvidence-source-licenses.txt).

Copyright © 2026 Medo. Distributed under the proprietary Free or Plus license in [LICENSE.md](https://ragvidence.medo-id.com/ragvidence-0.1.0-license.txt).
