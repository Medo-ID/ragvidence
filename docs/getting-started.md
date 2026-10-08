# Getting started

This tutorial explains the complete retrieval-debugging loop. It is intentionally local, deterministic, and small enough to inspect by hand.

## 1. Check the installation

From an extracted customer archive:

```bash
uv sync --frozen
uv run raglab health
```

From a tool installation:

```bash
raglab health
```

`PASS` means the core workflow is ready. A warning that the semantic extra is unavailable does not block the offline BM25 tutorial.

## 2. Run the guided tutorial

Use `uv run raglab` instead of `raglab` below when working directly from the source archive.

```bash
raglab tutorial
```

The command creates `workspaces/first-run` and runs two controlled experiments:

1. **Baseline:** search only the chunk body.
2. **Intervention:** search the same body prefixed with its authentic heading path.

The dataset, questions, retrieval strategy, evidence labels, and `k` remain fixed. Only the searchable representation changes.

## 3. Open the report

The report is written to:

```text
workspaces/first-run/reports/tutorial.html
```

On WSL:

```bash
explorer.exe "$(wslpath -w "$PWD/workspaces/first-run/reports/tutorial.html")"
```

On macOS:

```bash
open workspaces/first-run/reports/tutorial.html
```

On Linux desktop environments:

```bash
xdg-open workspaces/first-run/reports/tutorial.html
```

Opening the file does not upload it. It is a self-contained local report.

## 4. Read the report in the right order

1. Compare the baseline and intervention success rates.
2. Check **Pass → Fail** first; these are regressions.
3. Inspect **Fail → Pass** questions and their ranked hits.
4. Verify that improvement came from authentic source context, not leaked labels.
5. Read the diagnosis as a bounded hypothesis, not a universal conclusion.
6. Read the limitations and reproducibility metadata before sharing the result.

The primary metric is **sufficient evidence at k**. A question passes only when the first `k` retrieved units collectively contain every required evidence ID.

## 5. Inspect one retrieval manually

```bash
raglab inspect workspaces/first-run/runs/bm25-body.json --question DEV-01

raglab inspect workspaces/first-run/runs/bm25-heading_context.json --question DEV-01
```

This lets you see what moved in the ranking before relying on aggregate metrics.

## 6. Continue with your own data

Read [Bring your own data](bring-your-own-data.md), then create a clean experiment:

```bash
raglab init my-experiment
```

Do not replace the tutorial files with sensitive production data. Use a separate named workspace.

## Running the tutorial again

Existing outputs are never silently overwritten. Preserve the current tutorial and create a separately named copy:

```bash
raglab tutorial --name first-run-2
```
