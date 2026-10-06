# RAG Debugging Lab

RAG Debugging Lab is a local, CLI-first kit for finding retrieval failures with reviewed evidence instead of guessing from generated answers. It runs without an account, telemetry or a paid API.

The guided exercise compares the same questions under two representations:

- body-only chunks;
- the same bodies enriched with their authentic heading paths.

It supports BM25, optional local semantic retrieval and ranked results imported from another RAG stack. The evidence-level evaluator reports improvements, regressions and incomplete multi-evidence retrieval at the actual context depth `k`.

## Requirements

- Python 3.12 (pinned by `.python-version`)
- [`uv`](https://docs.astral.sh/uv/)
- About 100 MB for the core installation
- Additional model/download space only when semantic retrieval is enabled

## Five-minute start

```bash
uv sync --frozen
uv run raglab health
uv run raglab quickstart
uv run raglab validate workspaces/heading-context
uv run raglab benchmark workspaces/heading-context --strategies bm25 --k 2
```

Inspect the motivating result:

```bash
uv run raglab inspect \
  workspaces/heading-context/runs/bm25-body.json \
  --question DEV-01

uv run raglab inspect \
  workspaces/heading-context/runs/bm25-heading_context.json \
  --question DEV-01
```

After the evaluation-metrics contribution is integrated:

```bash
uv run raglab evaluate workspaces/heading-context \
  workspaces/heading-context/runs/bm25-body.json

uv run raglab evaluate workspaces/heading-context \
  workspaces/heading-context/runs/bm25-heading_context.json

uv run raglab compare \
  workspaces/heading-context/evaluations/bm25-body.json \
  workspaces/heading-context/evaluations/bm25-heading_context.json \
  workspaces/heading-context/comparisons/bm25.json

uv run raglab diagnose workspaces/heading-context/comparisons/bm25.json
```

Every output is local. Existing runs and reports are never silently overwritten.

## Optional semantic retrieval

```bash
uv sync --frozen --extra semantic
uv run raglab benchmark workspaces/heading-context \
  --strategies semantic --k 2
```

The first run downloads the selected FastEmbed model. Document vectors are cached inside the experiment workspace and subsequent matching runs reuse them. The default model and this exercise are English-focused; do not generalize results to another language without testing it.

To use your own Ollama or OpenAI-compatible embedding endpoint, copy `.env.example` to `.env`, set the provider values, then pass `--provider ollama` or `--provider openai_compatible`. The CLI displays a disclosure before sending source text or questions. No model access is provided by this product.

Optional answer inspection uses the same user-owned approach:

```bash
uv run raglab generate workspaces/heading-context \
  workspaces/heading-context/runs/bm25-heading_context.json \
  workspaces/heading-context/answers.json
```

Configure `RAGLAB_GENERATION_PROVIDER`, model, base URL and optional API key first. Generated answers remain separate from retrieval evaluation.

## Use your own data

```bash
uv run raglab init my-experiment
```

Edit `workspaces/my-experiment/sources.jsonl` and `questions.jsonl`, then run `validate` before benchmarking. Read [Bring your own data](docs/bring-your-own-data.md) for schemas, labeling guidance and leakage warnings.

## Evaluate an existing retriever

Export one JSON object per question with ranked source IDs:

```json
{"question_id":"Q-001","hits":[{"source_unit_id":"S-17","rank":1,"score":0.82}]}
```

```bash
uv run raglab import-run workspaces/my-experiment results.jsonl \
  --name my-production-retriever --k 2
```

The lab enriches imported source IDs with your reviewed evidence labels. It does not require LangChain, LlamaIndex or a vector database.

## Recovery

If experiment files are broken:

```bash
uv run raglab workspace restore my-experiment
```

The current directory is moved to a timestamped backup before a clean copy is created. It is never deleted automatically. Internal package edits should be recovered from version control or a fresh release archive.

## Trust boundary

- Retrieval metrics evaluate whether reviewed evidence was retrieved; they do not prove answer correctness.
- Unanswerable questions are `N/A` in this first exercise; no abstention claim is made.
- The teaching dataset is small, fictional and constructed to expose a known failure.
- Timing on this dataset is descriptive, not a scalability benchmark.
- Heading enrichment is one controlled intervention, not a universal best practice.

See [Privacy and providers](docs/privacy-and-providers.md), [Interpreting results](docs/interpreting-results.md) and [Troubleshooting](docs/troubleshooting.md).

## Development

```bash
uv sync --dev
uv run ruff check src tests
uv run pytest
uv run raglab verify
```

`verify` remains blocked until the owner-contributed metrics and HTML template are integrated. Their contracts are in `docs/contributing-metrics.md` and `docs/html-template-contract.md`.
