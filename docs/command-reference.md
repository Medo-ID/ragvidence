# Command reference

Use `raglab COMMAND --help` for the authoritative options installed with your version.

| Command | Purpose |
| --- | --- |
| `raglab health` | Check Python, dependencies, bundled data, workspace access, semantic support, and local privacy defaults. |
| `raglab edition` | Show the installed Free or Plus edition and its activation requirement. |
| `raglab verify` | Run deterministic release and installation fixtures. |
| `raglab tutorial` | Run the complete first-use BM25 comparison and create an HTML report. |
| `raglab quickstart` | Copy only the bundled heading-context exercise. |
| `raglab init NAME` | Create a named editable experiment. |
| `raglab validate WORKSPACE` | Validate schemas, unique IDs, answerability, and evidence references. |
| `raglab benchmark WORKSPACE` | Run body and heading-context retrieval configurations. |
| `raglab inspect RUN --question ID` | Inspect ranked evidence for one question. |
| `raglab import-run WORKSPACE FILE --name NAME` | Normalize ranked results from an external retriever. |
| `raglab evaluate WORKSPACE RUN` | Calculate evidence-level metrics. |
| `raglab compare BASELINE INTERVENTION OUTPUT` | Classify every question as improvement, regression, stable pass, or stable failure. |
| `raglab diagnose COMPARISON` | Explain a bounded observed pattern and propose a next experiment. |
| `raglab report BASELINE OUTPUT` | Export JSON, Markdown, or HTML; optionally add `--intervention`. |
| `raglab generate WORKSPACE RUN OUTPUT` | Generate optional answers with a user-configured provider. |
| `raglab workspace restore NAME` | Back up a managed workspace and replace it with a clean exercise. |

## Common options

```bash
raglab benchmark --help
raglab report --help
raglab workspace restore --help
```

`--root` changes the managed workspace directory for commands that create or restore workspaces. Output files are never silently overwritten.
