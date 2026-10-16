# Install and update RAGvidence

Install the CLI once, then run `ragvi` from any folder containing your data.
You do not need a Python project, workspace or RAG framework to use the portable
commands. The CLI is fully free under [Apache-2.0](../LICENSE.md).

## Install the global command

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) using the
   instructions for Windows, macOS or Linux. Open a new terminal afterward.
2. Install RAGvidence using Python 3.12; uv can download that Python version:

```bash
uv tool install --python 3.12 "ragvidence==0.2.0"
```

3. Check the installation:

```bash
ragvi --version
ragvi health
ragvi verify
```

`verify` runs bundled deterministic checks without downloading a model. A missing
optional semantic runtime does not block BM25. If `ragvi` is not on PATH, run
`uv tool update-shell`, restart your terminal and try again.

Python 3.12 is the supported version. Automated installed-package checks cover
Linux x64, Windows x64, macOS Apple Silicon and macOS Intel. They do not establish
support for every OS version, architecture or model/hardware combination.

## Install this update

For an existing uv tool installation:

```bash
uv tool install --upgrade --python 3.12 "ragvidence==0.2.0"
ragvi --version
ragvi verify
```

Include any extras you use in the package specification, for example
`"ragvidence[pdf,semantic]==0.2.0"`. Keep your experiment folders and reports;
updating the tool does not require deleting them. Use a new output directory when
running another experiment.

## Optional PDF support

```bash
uv tool install --reinstall --python 3.12 "ragvidence[pdf]==0.2.0"
```

This adds text extraction for text-bearing PDFs. Scans, OCR and visual table/layout
interpretation are not included. The report records extraction warnings and page
locations.

## Optional model support

For local FastEmbed embeddings, cross-encoder reranking or MMR:

```bash
uv tool install --reinstall --python 3.12 "ragvidence[semantic]==0.2.0"
ragvi semantic ./docs --query "How do I reset the device?"
```

The first run downloads the selected model, then inference runs locally. Allow
disk space and memory for that model. `--cache-dir DIRECTORY` selects the model
and vector cache location.

Install both extras together with `"ragvidence[pdf,semantic]==0.2.0"`.
Reinstalling replaces the tool environment; include every extra you need.

You can also use a running Ollama service or an OpenAI-compatible endpoint for
embeddings. After making your chosen Ollama embedding model available, create
`providers.env` with your service URL:

```dotenv
RAGVIDENCE_EMBEDDING_BASE_URL=http://localhost:11434
```

Then select the model explicitly:

```bash
ragvi semantic ./docs --env-file ./providers.env --provider ollama --model YOUR_EMBEDDING_MODEL --query "Reset procedure"
```

Portable commands load dotenv files only when selected with `--env-file`.
See the [provider guide](user-guide.md#openai-compatible-embeddings) for
OpenAI-compatible settings; use the same explicit env-file flag on portable runs.

For question rewriting and model-selected compression, configure a chat model
separately. See [advanced techniques](portable-advanced-techniques.md) for provider
flags, environment variables and bounded requests. These adapters use your model
server or API access; the CLI does not install that server or provide API credits.
Remote endpoints receive source/query text as described in
[privacy and providers](privacy-and-providers.md).

## Install from source

From a clone or extracted source distribution:

```bash
uv sync --frozen
uv run ragvi --version
uv run ragvi verify
```

Use `uv run ragvi` inside that checkout. To build and install its global command:

```bash
uv build --out-dir dist/release
uv tool install --python 3.12 ./dist/release/ragvidence-0.2.0-py3-none-any.whl
```

Use `--reinstall` deliberately when replacing an existing global installation.
Contributor checks are described in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Next: your first experiment

Follow [getting started](getting-started.md) to run on your own file, open the
report and compare two techniques. Use `ragvi techniques` to see prerequisites
before selecting a model-backed technique.
