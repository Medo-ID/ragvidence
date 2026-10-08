# User guide

This guide covers supported workflows beyond the bundled tutorial. Commands use an installed `raglab` tool. Prefix them with `uv run` when using the source archive.

## The experiment lifecycle

Every useful experiment follows the same sequence:

1. Create and validate a labeled workspace.
2. Run a baseline retrieval configuration.
3. Change one meaningful variable.
4. Evaluate both runs at the same `k`.
5. Compare improvements and regressions.
6. Inspect changed rankings.
7. Export a report with limitations and metadata.

## Create a custom experiment

```bash
raglab init customer-support
```

Edit `workspaces/customer-support/sources.jsonl` and `questions.jsonl`, then validate:

```bash
raglab validate workspaces/customer-support
```

Start with 10–50 source units and 10–30 carefully reviewed questions. Larger weakly labeled datasets create more confident-looking noise, not stronger evidence. See [Bring your own data](bring-your-own-data.md) for schemas and labeling rules.

## BM25 representation comparison

```bash
raglab benchmark workspaces/customer-support --strategies bm25 --k 4

raglab evaluate workspaces/customer-support \
  workspaces/customer-support/runs/bm25-body.json

raglab evaluate workspaces/customer-support \
  workspaces/customer-support/runs/bm25-heading_context.json
```

Compare and diagnose:

```bash
raglab compare \
  workspaces/customer-support/evaluations/bm25-body.json \
  workspaces/customer-support/evaluations/bm25-heading_context.json \
  workspaces/customer-support/comparisons/bm25.json

raglab diagnose workspaces/customer-support/comparisons/bm25.json
```

Create a shareable HTML report:

```bash
raglab report \
  workspaces/customer-support/evaluations/bm25-body.json \
  workspaces/customer-support/reports/bm25-comparison.html \
  --intervention workspaces/customer-support/evaluations/bm25-heading_context.json \
  --format html
```

## Semantic retrieval

Install optional local semantic dependencies into a tool installation:

```bash
uv tool install --reinstall "rag-debugging-lab[semantic]"
```

For a source archive:

```bash
uv sync --frozen --extra semantic
```

Run the default local embedding model:

```bash
raglab benchmark workspaces/customer-support \
  --strategies semantic \
  --k 4
```

The first run downloads the selected model. Embeddings are cached inside the workspace and reused when the model and searchable text match. The default model is English-focused; evaluate any model on the language and document style you actually use.

### Ollama embeddings

Copy `.env.example` to `.env` and configure:

```dotenv
RAGLAB_EMBEDDING_PROVIDER=ollama
RAGLAB_EMBEDDING_MODEL=your-embedding-model
RAGLAB_EMBEDDING_BASE_URL=http://localhost:11434
```

```bash
raglab benchmark workspaces/customer-support \
  --strategies semantic \
  --provider ollama \
  --model your-embedding-model \
  --k 4
```

### OpenAI-compatible embeddings

Configure `.env`:

```dotenv
RAGLAB_EMBEDDING_PROVIDER=openai_compatible
RAGLAB_EMBEDDING_MODEL=your-model
RAGLAB_EMBEDDING_BASE_URL=https://provider.example/v1
RAGLAB_EMBEDDING_API_KEY=your-key
```

Then run with `--provider openai_compatible`. Source text and questions will be sent to that endpoint. Review the provider’s retention and training policy first.

## Compare lexical and semantic retrieval

```bash
raglab benchmark workspaces/customer-support \
  --strategies bm25,semantic \
  --k 4
```

This produces four runs: body and heading-context for both strategies. Evaluate the specific pair representing the decision you are testing. Avoid changing strategy, representation, model, labels, and `k` in a single comparison because you will not know which change caused the result.

## Import an existing retriever

Export one JSON object per question:

```json
{"question_id":"Q-001","hits":[{"source_unit_id":"S-17","rank":1,"score":0.82}]}
```

Every question and source ID must match the reviewed workspace.

```bash
raglab import-run \
  workspaces/customer-support \
  exported-results.jsonl \
  --name production-v1 \
  --k 4

raglab evaluate \
  workspaces/customer-support \
  workspaces/customer-support/runs/production-v1.json
```

This is the recommended path for evaluating LangChain, LlamaIndex, a vector database, or a custom production retriever without rebuilding it inside the lab.

## Optional answer inspection

Answer generation is deliberately separate from retrieval scoring. Configure `ollama` or `openai_compatible` in `.env`:

```dotenv
RAGLAB_GENERATION_PROVIDER=ollama
RAGLAB_GENERATION_MODEL=your-chat-model
RAGLAB_GENERATION_BASE_URL=http://localhost:11434
```

```bash
raglab generate \
  workspaces/customer-support \
  workspaces/customer-support/runs/bm25-heading_context.json \
  workspaces/customer-support/answers/bm25-heading_context.json
```

Generated answers are inspection artifacts. They do not alter retrieval labels or scores.

## Report formats

Use `--format json` for automation, `markdown` for lightweight review, and `html` for a self-contained report teammates can open locally. Never share a report before checking source identifiers and previews for confidential content.

## Reproducibility rules

- Freeze the question set before evaluating an intervention.
- Design changes on `dev`; inspect `heldout` only after the intervention is frozen.
- Keep `k` identical across a comparison.
- Record model and provider names.
- Treat cached embeddings as invalid when the model or searchable text changes.
- Never silently replace run artifacts; use new names or a fresh workspace.

## Recovery

```bash
raglab workspace restore customer-support
```

The existing workspace becomes a timestamped backup. Restoration never deletes it automatically.
