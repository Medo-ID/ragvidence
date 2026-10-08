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

### Customer release archive

Extract the release, open a terminal in its directory, and run:

```bash
uv sync --frozen
uv run ragvidence health
uv run ragvidence tutorial
```

During source-based use, prefix commands with `uv run`. After installing the CLI as a tool, use `ragvidence` directly.

### Install a built wheel

```bash
uv tool install ./ragvidence-0.1.0-py3-none-any.whl
ragvidence health
ragvidence tutorial
```

Python 3.12 is pinned in `.python-version`; `uv` can install the required Python runtime automatically.

## First report

The tutorial writes a complete comparison to:

```text
workspaces/first-run/reports/tutorial.html
```

Open it in any browser. It contains the baseline, intervention, changed questions, diagnosis, ranked evidence, limitations, and reproducibility metadata.

Then follow [Getting started](docs/getting-started.md) to understand the experiment rather than only running it.

## Supported workflows

| Goal | Start here |
| --- | --- |
| Learn the workflow on bundled data | `ragvidence tutorial` |
| Evaluate your own labeled dataset | [Bring your own data](docs/bring-your-own-data.md) |
| Compare BM25 and semantic retrieval | [User guide](docs/user-guide.md#semantic-retrieval) |
| Test an existing RAG retriever | [User guide](docs/user-guide.md#import-an-existing-retriever) |
| Generate optional answers for inspection | [User guide](docs/user-guide.md#optional-answer-inspection) |
| Understand each metric | [Interpreting results](docs/interpreting-results.md) |
| Recover a broken workspace | [Troubleshooting](docs/troubleshooting.md) |
| Review data and provider boundaries | [Privacy and providers](docs/privacy-and-providers.md) |

The complete CLI reference is in [Command reference](docs/command-reference.md).

## What is included

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

The current release contains the complete Free feature set. Plus is a separate paid entitlement for advanced features released in Plus builds; features are never advertised as available until they ship. See [Plans and editions](docs/plans.md) and [LICENSE.md](LICENSE.md).

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
uv run ragvidence verify
uv build
```

See [Security](SECURITY.md), [Support](SUPPORT.md), [Changelog](CHANGELOG.md), [Third-party notices](THIRD_PARTY_NOTICES.md), and the [resolved dependency inventory](THIRD_PARTY_LICENSES.md).

Copyright © 2026 Medo. Distributed under the proprietary Free or Plus license in [LICENSE.md](LICENSE.md).
