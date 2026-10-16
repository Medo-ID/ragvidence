# Getting started

RAGvidence helps you inspect retrieval evidence and compare techniques on your own
files. These instructions cover **0.2.0** and matching source builds. The older
0.1.0 package has the earlier workspace workflow. Check `ragvi --version` and
[the README](../README.md) for current release/install availability.

## Check the installation

```bash
ragvi --version
ragvi health
ragvi verify
```

Python 3.12 is required. BM25 needs no model, account or API key. A warning that the
optional semantic runtime is missing does not block BM25. From a source checkout,
run `uv sync --frozen` and prefix commands with `uv run`.

## Inspect your own data

Run from a folder containing a supported file or directory:

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
ragvi bm25 ./docs --questions ./questions.txt --format html --format json
```

TXT question files contain one question per nonblank line. Supported inputs also
include Markdown, visible-text HTML, document JSON/JSONL, CSV and, with the `pdf`
extra, text-bearing PDFs. See [portable files](portable-file-usage.md) for schemas,
limits and extraction behavior. No workspace setup is needed for these commands.

The CLI prints ranked passages and report paths. By default, it creates a unique
run directory under `ragvi-reports/` and writes a self-contained HTML report.
Open the printed HTML path in your browser. Use `--format json`, `html` or
`markdown` repeatedly to select exports, and `--output DIRECTORY` to choose a root.
Your source files remain unchanged.

With sources only, the tool produces ingestion/chunk diagnostics. With questions,
it shows retrieval/context inspection. Quality metrics require
[reviewed original-span references](portable-techniques.md); the tool does not
invent relevance labels or a quality score from a document alone.

## Compare alternatives

```bash
ragvi techniques
ragvi compare-data ./docs --questions ./questions.txt --techniques bm25,parent-child
```

The techniques share frozen input and questions. Without reviewed references,
compare the returned passages and resources without treating the report as a
scored quality winner. Add `--reviewed FILE` for evidence-level evaluation.
See [comparisons](portable-comparisons.md) for suites, dev/heldout selection,
intervals, an existing-system baseline and validated resume.

Read regressions as well as improvements, check actual question counts and final
contexts, and review limitations before adopting a technique in your own RAG
system. The CLI provides diagnostic evidence; it does not change that system or
establish generated-answer/citation correctness.

## Try the fictional tutorial

```bash
ragvi tutorial
```

This optional teaching workflow compares body and authentic heading-context BM25
at a fixed `k` on bundled reviewed data. Its HTML report is written to
`workspaces/first-run/reports/tutorial.html`. The small fictional English dataset
explains the workflow; it is not a general benchmark.

The tutorial refuses to overwrite an existing workspace. Repeat it with a new name:

```bash
ragvi tutorial --name first-run-2
```

The earlier reviewed-workspace commands remain available. See the
[user guide](user-guide.md) and [bring your own reviewed data](bring-your-own-data.md).

## Models and sharing

Local FastEmbed models require the optional `semantic` runtime and a first model
download. User-owned Ollama and OpenAI-compatible endpoints are supported for
selected operations; see [advanced techniques](portable-advanced-techniques.md).
The tool does not install a chat-model server or provide API credits.

Reports can contain full source passages, questions, prompts and model output.
Review or regenerate them with sanitized data before sharing. Keep internal frozen
artifacts private when they contain the original corpus or reviewed references.
See [privacy and providers](privacy-and-providers.md) and
[troubleshooting](troubleshooting.md) for details.
