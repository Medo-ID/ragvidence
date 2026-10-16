# Getting started

Use RAGvidence to see what a retrieval technique finds in your data and compare
alternatives before implementing them in your RAG project. Start with BM25 and
parent-child retrieval; both run without a model or API key.

## Install and check the CLI

Follow the [installation guide](installation.md), then open a terminal:

```bash
ragvi --version
ragvi health
ragvi verify
```

Python 3.12 is required. BM25 needs no model, account or API key. A warning that the
optional semantic runtime is missing does not block BM25. From a source checkout,
run `uv sync --frozen` and prefix commands with `uv run`.

## Prepare your data

Choose a small file or folder that represents the content your RAG system needs
to search. Keep questions in a separate UTF-8 `questions.txt` file, one per line.
For a first experiment, you can create `manual.txt` containing:

```text
Hold the reset button for eight seconds. Use USB-C power.
```

Choose questions that reflect real user needs, such as "How do I reset the device?"
Start small enough to check the returned passages yourself.

## Inspect retrieval

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

To inspect extraction and chunks without running retrieval, use:

```bash
ragvi bm25 ./manual.txt --no-input
```

With questions, the report shows retrieval/context inspection. Quality metrics require
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

## Read the report and choose your next test

1. Check the status, loaded/skipped files, settings and question counts.
2. Inspect the exact returned context. Does it include the conditions and details
   needed to answer the original question? Ranking scores are not probabilities.
3. With reviewed references, examine regressions as well as improvements. Check
   whether the context contains every required evidence span.
4. Compare context size and observed timing alongside quality. Missing costs or
   timing measurements remain unavailable.
5. Test a relevant alternative or setting using the same questions and budget.
   Reserve separate heldout questions before drawing conclusions.

For example, parent-child retrieval may restore surrounding details but use more
context. Hybrid retrieval can combine lexical and semantic matches; it requires
an embedding provider. `ragvi techniques` lists each preset's requirements.
See [interpreting results](interpreting-results.md) for evidence metrics and limits.

The CLI provides evidence for your decision. It does not change your RAG system
or establish generated-answer/citation correctness.

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

For manually labeled source units and explicit run/evaluate/report steps, see the
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
