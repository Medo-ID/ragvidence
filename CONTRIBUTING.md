# Contributing to RAGvidence

RAGvidence is a free Apache-2.0 CLI that diagnoses and compares RAG retrieval
techniques on users' local data. Contributions should help users inspect evidence
and choose techniques for their projects. The CLI does not modify production RAG
systems or guarantee that a technique improves retrieval or generated answers.

## Start a contribution

Use [issues](https://github.com/Medo-ID/ragvidence/issues) for reproducible bugs,
questions and proposals. For a substantial technique or architecture change,
describe the diagnostic question, required input and expected evidence first.
Small documentation corrections can go directly to a pull request.

Use synthetic data in issues, tests and reports. Include the installed version,
OS/architecture, Python version, exact command, and expected versus observed
behavior. Reports and frozen artifacts can contain full source text and prompts;
review them before sharing. Security reports follow [SECURITY.md](SECURITY.md).

## Local setup

You need Git and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Use Windows, macOS or Linux with Python 3.12; uv can install Python for you.
Initial setup downloads Python/dependencies. The default test suite needs no
API key, running model service or downloaded model weights.

Fork [Medo-ID/ragvidence](https://github.com/Medo-ID/ragvidence) on GitHub, then
clone your fork and create a branch:

```bash
git clone https://github.com/YOUR_USERNAME/ragvidence.git
cd ragvidence
git remote add upstream https://github.com/Medo-ID/ragvidence.git
git switch -c fix/my-change
uv python install 3.12
uv sync --frozen --dev --all-extras
uv run --no-sync ragvi --version
uv run --no-sync ragvi verify
```

`uv sync` creates an isolated `.venv`; `uv run` selects its Python in each shell.
All extras install the PDF/semantic runtimes needed by the complete test suite;
this does not download model weights. Use `uv run --no-sync ragvi` while developing
so commands use this checkout. A separate global installation does not follow
your source edits.

Try the CLI against the bundled fictional input:

```bash
uv run --no-sync ragvi bm25 docs/examples/device-manual.md --questions docs/examples/questions.txt
```

Open the printed HTML path. Generated reports go to ignored `ragvi-reports/`.
For more commands and input schemas, see [getting started](docs/getting-started.md).

## Keep your local setup separate

The ignore rules cover virtual environments, editor/agent settings, local dotenv
files, credentials directories, caches, build output, logs, reports and generated
verification output. Use `local-data/` for personal datasets and
`verification/ci/` for new check results. Personal instructions, maintainer notes,
verification output, browser results, screenshots and recordings stay local and
ignored. Keep maintained tests and fixtures tracked; review report contents before
sharing them. Hosted CI retains its generated evidence as workflow artifacts.

Keep `pyproject.toml`, `uv.lock`, `.python-version`, `.env.example`, CI workflows,
tests/fixtures, documentation and license notices tracked. These define the
shared development environment. A file already tracked by Git is not removed by
adding an ignore rule; check staged changes before submitting them.

The normal local workflow needs no `.env`. If testing your own provider, copy
`.env.example` locally, fill only the needed settings and select it with
`--env-file .env` on portable commands. Keep credentials out of source and fixtures.

## Make your first change

Choose a focused bug, documentation correction or proposed diagnostic experiment.
Read the affected module and relevant tests, make the change, then run focused
checks before the complete validation below. For example:

```bash
uv run --no-sync pytest tests/unit/test_portable.py
```

When adding or updating dependencies intentionally, update the manifest, lock and
applicable notices together. Ordinary setup uses the existing frozen lock.

## Architecture and boundaries

| Area | Responsibility |
| --- | --- |
| `portable_cli.py`, `portable_config.py`, `capabilities.py` | Commands, option resolution, presets and requirements |
| `ingestion/`, `questions.py` | Supported local inputs, extracted text/locations and independent questions |
| `portable.py`, `pipeline.py`, `runner.py` | Shared orchestration and stage construction/execution |
| `strategies/`, `providers/` | Retrieval algorithms and model/service adapters |
| `evaluation/`, `context.py`, `compression.py` | Original-span scoring and final context transformations |
| `suites/` | Frozen comparisons, dev/heldout policy, intervals and validated resume |
| `artifacts.py`, `reporting/` | Canonical storage and consistent JSON/Markdown/HTML presentation |

Keep functions focused on one responsibility. Reuse shared stages, provider
contracts, storage and rendering; avoid a separate scoring or ranking path for
each CLI command. Preserve source-relative offsets, original question intent,
strict validation and explicit missing/failed/not-run states. Reviewed labels and
reference answers must not reach retrieval or transformation prompts.

## Validation

Run focused tests while working, then the ordinary checks:

```bash
uv run --no-sync ruff check src tests scripts
uv run --no-sync pytest tests
uv run --no-sync ragvi verify
```

Core pytest blocks external network requests. Explicitly marked loopback HTTP
fixtures test adapter contracts with synthetic responses. They do not establish
that a real model follows the contract or provides useful retrieval evidence.

For a release or a change to packaging/portable workflows, use the shared gate:

```bash
uv run --no-sync python -m scripts.verify_release --online-install
```

It checks target dependency availability, tests and capability contracts, builds
and inspects distributions, then exercises isolated wheel/source/optional-runtime
installations from unrelated data folders. `--online-install` allows fetching
locked package metadata/dependencies; it does not enable model downloads or
external access in unit tests. A fully warm resolver cache can run without it.
CI repeats the gate and an upgrade check on Linux x64, Windows x64 and macOS
ARM64/Intel. Other Python/OS/model combinations are outside that tested matrix.
See [the release procedure](docs/releasing.md) for packaging, publication and
installed-release checks.

For a bug, add a regression for the observed failure when appropriate. For a
technique, include an independently computed positive case, an adverse or neutral
case, provenance assertions, and a command-to-report journey. Update the catalog,
`scripts/capability_contracts.json`, its required-contract guard and the coverage
guide together. Test final evidence after budgets/compression; do not assume an
intervention must help. Do not write tests that only repeat implementation logic.

Real-model checks are separate. Use the documented pinned local files/digests and
record actual quality outcomes, including failures. Do not require contributors
to supply API credentials or download a large model for the default unit suite.
Fixture contracts cannot establish universal model quality, language coverage or
hardware support.

## Pull requests and licensing

Review your changes and push your branch to your fork:

```bash
git diff --check
git status --short
git add PATH_TO_CHANGED_FILE
git diff --cached
git commit -m "Describe the change"
git push -u origin fix/my-change
```

Use your own Git author identity for your contributions. Open a pull request to
`Medo-ID/ragvidence:main` and wait for CI. Update your branch to address review or
check failures; tests run on Linux, Windows and macOS. The project supplies the
issue forms and PR template in `.github/`.

Explain the concrete problem, resulting behavior and validation you performed.
Keep changes scoped, disclose limitations and update affected help/docs/examples.
Do not change artifact schemas/hashes or dependency versions incidentally; explain
compatibility and update the lock/notices when those changes are necessary.
Use respectful, constructive discussion. Maintainers review scope and evidence
before merging; opening an issue does not promise delivery or a response deadline.

Intentional contributions are submitted under this project's Apache-2.0 license
unless a separate arrangement is agreed in advance. Preserve third-party and
model/font notices. Starring, sharing, reporting bugs and improving documentation
are welcome ways to support the project.
