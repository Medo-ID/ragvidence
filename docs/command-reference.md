# Command reference

Use `ragvidence COMMAND --help` for the authoritative options installed with your version.

| Command | Purpose |
| --- | --- |
| `ragvidence health` | Check Python, dependencies, bundled data, workspace access, semantic support, and local privacy defaults. |
| `ragvidence edition` | Show the installed Free or Plus edition and its activation requirement. |
| `ragvidence verify` | Run deterministic release and installation fixtures. |
| `ragvidence tutorial` | Run the complete first-use BM25 comparison and create an HTML report. |
| `ragvidence quickstart` | Copy only the bundled heading-context exercise. |
| `ragvidence init NAME` | Create a named editable experiment. |
| `ragvidence validate WORKSPACE` | Validate schemas, unique IDs, answerability, and evidence references. |
| `ragvidence benchmark WORKSPACE` | Run body and heading-context retrieval configurations. |
| `ragvidence inspect RUN --question ID` | Inspect ranked evidence for one question. |
| `ragvidence import-run WORKSPACE FILE --name NAME` | Normalize ranked results from an external retriever. |
| `ragvidence evaluate WORKSPACE RUN` | Calculate evidence-level metrics. |
| `ragvidence compare BASELINE INTERVENTION OUTPUT` | Classify every question as improvement, regression, stable pass, or stable failure. |
| `ragvidence diagnose COMPARISON` | Explain a bounded observed pattern and propose a next experiment. |
| `ragvidence report BASELINE OUTPUT` | Export JSON, Markdown, or HTML; optionally add `--intervention`. |
| `ragvidence generate WORKSPACE RUN OUTPUT` | Generate optional answers with a user-configured provider. |
| `ragvidence workspace restore NAME` | Back up a managed workspace and replace it with a clean exercise. |

## Common options

```bash
ragvidence benchmark --help
ragvidence report --help
ragvidence workspace restore --help
```

`--root` changes the managed workspace directory for commands that create or restore workspaces. Output files are never silently overwritten.
