# Troubleshooting

## `ragvidence: command not found`

When working from the source archive, use:

```bash
uv sync --frozen
uv run ragvidence health
```

When installing the wheel as a CLI tool, use:

```bash
uv tool install ./rag_debugging_lab-0.1.0-py3-none-any.whl
ragvidence health
```

If `uv` warns that its tool binary directory is not on `PATH`, run `uv tool update-shell`, restart the terminal, and retry.

## `health` reports the wrong Python version

Run commands through `uv`, which installs the pinned Python 3.12 environment:

```bash
uv sync --frozen
uv run ragvidence health
```

## Semantic retrieval says the extra is missing

```bash
uv sync --frozen --extra semantic
```

The first semantic run also needs network access to download its model. BM25 remains available offline.

## A run already exists

The lab refuses silent overwrite. Rename/archive the old run or create a fresh workspace. This protects reproducibility.

## Validation reports an unknown evidence ID

Every ID in `required_evidence_ids` must appear in at least one source unit’s `evidence_ids`. Fix the annotation rather than weakening validation.

## Results improve only at a large k

That may not help the real application. Repeat the experiment at the context depth the application actually uses and report the limitation.

## I broke the workspace

Run `ragvidence workspace restore NAME`. Your current workspace becomes a timestamped backup. Package source-code edits require version control or a fresh release archive.

## A report might contain private data

Do not share it yet. HTML reports contain short retrieved previews by design. Create a sanitized dataset/run and regenerate the report; do not manually edit authoritative evaluation JSON to hide data.
