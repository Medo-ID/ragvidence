# Command reference

Use `ragvi COMMAND --help` for the authoritative options installed with your version.

| Command | Purpose |
| --- | --- |
| `ragvi health` | Check Python, dependencies, bundled data, workspace access, semantic support, and local privacy defaults. |
| `ragvi edition` | Show the installed Free or Plus edition and its activation requirement. |
| `ragvi verify` | Run deterministic release and installation fixtures. |
| `ragvi tutorial` | Run the complete first-use BM25 comparison and create an HTML report. |
| `ragvi quickstart` | Copy only the bundled heading-context exercise. |
| `ragvi init NAME` | Create a named editable experiment. |
| `ragvi validate WORKSPACE` | Validate schemas, unique IDs, answerability, and evidence references. |
| `ragvi bm25 INPUT` | Development build: inspect TXT/Markdown, HTML, document JSON/JSONL, CSV or optional text PDFs and export reports without workspace setup. |
| `ragvi benchmark WORKSPACE` | Run body and heading-context retrieval configurations. |
| `ragvi experiment WORKSPACE CONFIG_FILE` | Run a JSON-configured retrieval pipeline with optional hybrid search, children, query variants and reranking. |
| `ragvi inspect RUN --question ID` | Inspect ranked evidence for one question. |
| `ragvi import-run WORKSPACE FILE --name NAME` | Normalize ranked results from an external retriever. |
| `ragvi evaluate WORKSPACE RUN` | Calculate evidence-level metrics. |
| `ragvi compare BASELINE INTERVENTION OUTPUT` | Classify every question as improvement, regression, stable pass, or stable failure. |
| `ragvi diagnose COMPARISON` | Explain a bounded observed pattern and propose a next experiment. |
| `ragvi report BASELINE OUTPUT` | Export JSON, Markdown, or HTML; optionally add `--intervention`. |
| `ragvi generate WORKSPACE RUN OUTPUT` | Generate optional answers with a user-configured provider. |
| `ragvi workspace restore NAME` | Back up a managed workspace and replace it with a clean exercise. |

## Common options

```bash
ragvi benchmark --help
ragvi report --help
ragvi workspace restore --help
```

`--root` changes the managed workspace directory for commands that create or restore workspaces. Output files are never silently overwritten.

See [Portable file usage](portable-file-usage.md) for `bm25` question flags,
automatic HTML output, JSON/Markdown selection and the distinction between
source diagnostics, unscored retrieval inspection and reviewed evaluation.

`benchmark --strategies` accepts `bm25`, `semantic`, and `hybrid`, separated by commas.
See [RAG technique coverage](rag-technique-coverage.md) for experiment settings,
examples, implementation limits and techniques still missing from the reference resource.
