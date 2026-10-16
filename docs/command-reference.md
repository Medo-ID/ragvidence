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
| `ragvi techniques` | List portable techniques and requirements; `--format json` for automation. |
| `ragvi semantic INPUT`, `ragvi hybrid INPUT` | Portable dense cosine or weighted lexical/dense fusion. |
| `ragvi rerank INPUT` | Portable cross-encoder reranking with an explicit model. |
| `ragvi parent-child INPUT` | Retrieve small children and return full original source units. |
| `ragvi heading-context INPUT`, `ragvi contextual INPUT` | Index authentic headings or supplied reviewed prefixes. |
| `ragvi multi-query INPUT` | Fuse original questions and supplied variants. |
| `ragvi metadata-filter INPUT` | Apply typed global/question metadata predicates before ranking. |
| `ragvi mmr INPUT` | Select relevant and diverse candidates with explicit cosine embeddings. |
| `ragvi rewrite INPUT`, `ragvi auto-multi-query INPUT` | Generate bounded question-only queries with a user-owned model. |
| `ragvi compress INPUT` | Return validated original spans using deterministic sentences or an optional model selector. |
| `ragvi import-data INPUT` | Verify external original-span results or explicitly limited ID-only proxies. |
| `ragvi compare-data INPUT` | Compare techniques on one frozen corpus with optional existing-system baseline, reviewed spans, grids and decision reports. |
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
See [Portable techniques](portable-techniques.md) for `--reviewed`, stage limits,
source-prefix/query-variant schemas, tokenizer budgets and exact context imports.
See [Portable comparisons](portable-comparisons.md) for `--techniques`, `--suite`,
`--phase`, `--shortlist`, `--resume`, intervals, criteria and supplied pricing.
See [Advanced retrieval techniques](portable-advanced-techniques.md) for `--filters`,
MMR, rewriting/compression flags, nested stage schemas and provider boundaries.

`benchmark --strategies` accepts `bm25`, `semantic`, and `hybrid`, separated by commas.
See [RAG technique coverage](rag-technique-coverage.md) for experiment settings,
examples, implementation limits and techniques still missing from the reference resource.
