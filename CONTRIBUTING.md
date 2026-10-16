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

Clone your fork, create a branch and install the locked Python 3.12 environment:

```bash
git clone https://github.com/YOUR_USERNAME/ragvidence.git
cd ragvidence
git switch -c fix/my-change
uv sync --frozen --dev --all-extras
uv run --no-sync ragvi --version
uv run --no-sync ragvi verify
```

Use `uv run --no-sync ragvi` while developing. A globally installed `ragvi` may
come from a different version and will not automatically use this checkout.
The older 0.1.0 release lacks the portable commands in this source; use the
version installed from your checkout when testing a contribution.

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

Explain the concrete problem, resulting behavior and validation you performed.
Keep changes scoped, disclose limitations and update affected help/docs/examples.
Do not change artifact schemas/hashes or dependency versions incidentally; explain
compatibility and update the lock/notices when those changes are necessary.
Use respectful, constructive discussion. Maintainers review scope and evidence
before merging; opening an issue does not promise delivery or a response deadline.

Intentional contributions are submitted under this project's Apache-2.0 license
unless a separate arrangement is agreed in advance. Preserve third-party and
model/font notices. No payment, donation or sponsorship is required to contribute
or use any included feature. Starring, sharing, reporting bugs and improving
documentation are welcome ways to support the project.
