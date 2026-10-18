# Website handoff: RAGvidence 0.2.0

Use this brief in the separate `../ragvidence-web` session. Follow that repository's
AGENTS.md, README and maintenance guidance, and preserve existing uncommitted work.
The execution order is in
[the completion checklist](docs/maintainer/release-and-website-checklist.md).
The CLI package release and repository setup are complete. Actions access was
restored; [PR #1](https://github.com/Medo-ID/ragvidence/pull/1) merged as `8af8d1f`,
and its PR and main CI runs passed. Website tasks 7–13 are next in the website
repository. Start that session by reviewing this brief and the checklist; verify
the website's current state before acting on earlier notes. Treat the CLI
repository and published release as read-only references during website work.

## Instructions for the website agent

Work in `../ragvidence-web`. Read its applicable AGENTS.md, README and maintenance
guidance, then inspect `git status` and the existing diff before editing. Preserve
and understand existing work; do not reset files or restore deleted assets blindly.

Follow checklist tasks 7–13 in order. Map each product claim and command example
to the published CLI's behavior and the technical sources below. Keep a concise
mapping in the website's maintenance documentation so future CLI changes have
known website/docs counterparts. Record the CLI version, release commit, wheel
hash and website commit used for examples/media. Use an isolated installation of
the production `ragvidence==0.2.0` wheel for command validation; do not rely on an
unreleased CLI checkout or change the user's global installation incidentally.

Update product copy, website documentation, release/license links, metadata,
examples, sample reports, media, maintenance guidance and affected tests together.
Focus on current supported functionality. Remove obsolete edition/paywall copy
and old install snippets; do not recount previous product decisions. Use actual
synthetic command outputs for reports and performance/quality claims. Never
invent scores, supported input types, model compatibility or technique coverage.

Use the website's declared Node/npm versions and required verification scripts.
Recheck the recorded reduced-motion failures on the current tree, fix real
failures, and pass lint, types, the normal production build, verifier and browser
tests, accessibility/responsive checks and the production dependency audit.
Do not weaken meaningful tests to make the gate pass. Commit as
**Medo-ID <midaghdour@gmail.com>**, push through the repository's required review
flow, and confirm CI. Keep generated private data and tool caches untracked.

Continue all work that can be completed in the website repository. Ask for missing
host/domain access or production-deployment authorization only when a concrete
preview and its verification are ready. Do not modify, republish or retag the CLI
to make website copy true. Report any actual CLI defect separately with a
reproduction. At the end, report website checks, commit/deployment identities,
live URLs and any remaining owner actions. The deferred human Windows CLI test
is not a blocker for starting website work.

## Product

RAGvidence is a fully free Apache-2.0 CLI for diagnosing and comparing RAG retrieval
techniques on users' own data. It saves users from implementing each experiment
before deciding what to use in their RAG projects.

Present the current product directly. Focus on what users need: install the CLI,
point it at data, ask questions, compare techniques and inspect/share evidence.
Keep the copy simple and explain what the current release includes.

Use one installation path and Source, Contribute and Star links. Sponsorship is
unconfigured and optional; omit a Sponsor/Donate button until a working destination
is supplied and verified. See [setup instructions](docs/maintainer/sponsorship.md).
Keep website licensing separate from the CLI license and retain asset notices.

## Technical sources

- `pyproject.toml`, `src/ragvidence/__init__.py`, `uv.lock`: version, Python 3.12
  requirement, `ragvi` entry point and `pdf` / `semantic` extras.
- Installed `ragvi --help`, `ragvi COMMAND --help`, `ragvi techniques --format json`
  and `src/ragvidence/capabilities.py`: actual commands, options and requirements.
- README, CHANGELOG and `docs/installation.md`, `docs/getting-started.md`,
  `docs/portable-file-usage.md`, `docs/portable-techniques.md`,
  `docs/portable-comparisons.md`, `docs/portable-advanced-techniques.md`,
  `docs/interpreting-results.md`, `docs/rag-technique-coverage.md`: supported use.
- `LICENSE.md`, NOTICE and third-party/model/font notices: licensing.
- `docs/maintainer/portable-implementation-evidence.md`, retained verification
  outcomes and the latest CI results: what was actually checked.

## Release availability

Version **0.2.0 is published on production PyPI** under Apache-2.0.
The annotated `v0.2.0` tag points to release commit
`fba0c92ddaeb414ba8e9f0dea0e0c93f4e9c29f4` (Medo-ID).

- Production: https://pypi.org/project/ragvidence/0.2.0/
- TestPyPI: https://test.pypi.org/project/ragvidence/0.2.0/
- GitHub release: https://github.com/Medo-ID/ragvidence/releases/tag/v0.2.0
- Production run: https://github.com/Medo-ID/ragvidence/actions/runs/39012063464
- TestPyPI run: https://github.com/Medo-ID/ragvidence/actions/runs/38938991864
- Both platform matrices and exact published-wheel checks passed. Wheel and
  source-distribution SHA-256 values match across both indexes:
  `ef300e798bc7cad72a560dc2a6c6c9819737bdbac9241f7ebf2a593a5f2c54e9` (wheel),
  `654a3ea0b1429ea72618501f205a97efb33965ff94775fe2f628f1ded008be0b` (source).

The GitHub Release is published. Its four attachments were downloaded and verified
byte for byte against the original production-run assets on 2026-10-17. The wheel
and source distribution also match both indexes; the checksum manifest and
provenance identify the clean release commit above. The original automatic release
job was skipped; manual completion and the subsequent workflow fix are recorded
in the checklist. Keep the published tag and package artifacts unchanged.
Until the website is deployed, use the working GitHub documentation URLs.

The maintainer deferred the human Windows check on 2026-10-17. Do not describe it
as passed. A synthetic manual-check ZIP is prepared in ignored `local-data/`;
its six command journeys passed on Linux. This is separate from human usability
review and the automated Windows/macOS runner checks.

```bash
uv tool install --python 3.12 "ragvidence==0.2.0"
ragvi --version
ragvi verify
```

Use the CLI installation guide for uv setup, upgrades, optional extras and source
builds. A global `ragvi` runs from any data folder; portable commands do not need
a Python project, RAG framework, database or manually prepared workspace.

## Core journey

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
ragvi bm25 ./docs --questions ./questions.txt --format html --format json
ragvi compare-data ./docs --questions ./questions.txt --techniques bm25,parent-child
ragvi techniques
```

TXT questions use one question per nonblank line. Question entry is offered on a
terminal when no questions are supplied. `--no-input` disables prompts;
`--interactive` offers report-format selection on a terminal. Format flags work
without prompts. Reports go under `ragvi-reports/`; `--output` selects a root.
HTML is self-contained and opens offline. Original files remain unchanged.

| Input | Result |
| --- | --- |
| Sources | Extraction/structure/chunk diagnostics |
| Sources and questions | Ranked passages, context, stage traces and resource inspection |
| Reviewed original-span references too | Evidence sufficiency, coverage, rank/precision metrics and paired gains/regressions |

Use real schema examples from the CLI docs. Questions alone do not create reviewed
relevance labels or a scored quality winner. Show failures and trade-offs alongside
improvements. Small samples do not establish a general best technique.

## Included capabilities

- Local UTF-8 TXT/Markdown, visible-text HTML, document JSON/JSONL, CSV and optional
  text-bearing PDFs, including mixed folders with discovery/extraction limits.
- BM25, dense cosine, weighted hybrid RRF, local cross-encoder reranking,
  parent-child retrieval, heading enrichment, supplied context prefixes and
  supplied multi-query fusion.
- Typed metadata filters, cosine MMR, bounded model query rewriting/multi-query
  generation, deterministic sentence extraction and model-selected exact spans.
- Recursive/ATX Markdown splitting, overlap, separate stage depths, context budgets
  and identified local tokenizer settings.
- Existing-retriever imports with original-span validation or clearly limited
  registered-unit proxies.
- Frozen comparisons, bounded suites/grids, paired intervals, dev shortlists before
  heldout evaluation, local heldout-reuse disclosure, partial failures and resume.
- Terminal summaries and HTML/JSON/Markdown reports, exact context, source locations,
  hashes, configuration and model/provider/stage evidence.
- A fictional tutorial and optional reviewed-workspace workflow. Answer generation
  is available for inspection, without answer/citation correctness scoring.

Explain experiments rather than inflating a catalog count into independent algorithms.

## Models, platforms and privacy

BM25 and sentence extraction need no LLM. FastEmbed embeddings/rerankers run locally
after model download. User-owned Ollama models and OpenAI-compatible endpoints can
be used for selected operations. The CLI does not install a model server or supply
API credits. Model requirements, output compliance and quality depend on the model
and hardware. An OpenAI-compatible endpoint can be local or remote.

Installed-package checks cover Linux x64, Windows x64 and macOS ARM64/Intel on
Python 3.12. The production run linked above passed on the exact released commit.
Post-release maintenance CI
[39135984400](https://github.com/Medo-ID/ragvidence/actions/runs/39135984400)
also passed on merged commit `8af8d1f`, including the workflow condition fix and
website handoff. Consult Actions for later documentation commits. Real-model
checks use identified Linux configurations and do not establish inference
compatibility on every OS.

Remote services receive the text needed for the selected operation. Reviewed
reference answers/evidence IDs are excluded from retrieval/transformation prompts.
Reports can contain full passages, questions, prompts and model output; internal
artifacts can contain the full corpus/references. Explain reviewing content before
sharing. HTML escapes source content and uses embedded fonts without remote assets.

## Scope limits

The CLI provides evidence for a user's choice; it does not modify or deploy their
RAG system. It does not judge generated answers, citations or abstention.
OCR/scanned PDFs, DOCX/spreadsheets, image/audio ingestion, crawling and database
connectors are not supported. Text extraction does not guarantee layout/table fidelity.
See the coverage guide for missing retrieval families. Supplied usage/pricing is
an estimate; unavailable timing/cost data must not become zero or a fabricated saving.

## Website acceptance

Update the landing page, docs, version badges, install/upgrade snippets, FAQs,
releases, trust/license pages, navigation, metadata/JSON-LD, downloadable notices,
terminal demo, sample report and media together. Keep current docs focused on the
current release. Audit links and tests for content being removed or replaced.

Generate reports/videos from the exact production release using synthetic data.
Record commands, settings, version and artifact/report hashes. Do not hand-edit
scores, omit regressions or imply the sample is an independent customer benchmark.

Review and preserve the website's existing cleanup. Resolve the recorded
reduced-motion failures and pass its complete `npm run verify` gate, including a
normal production build on a capable host, browser checks and production audit.
Verify a preview, then deploy as the separately authorized final action. Check the
live domain, HTTPS, docs/search, keyboard/mobile use, copy controls and media.

## Deferred work and owner decisions

The ordered website plan is tasks 7–13 of the completion checklist: reconcile the
existing changes; update product/trust pages; update docs and executable examples;
regenerate reports and media; pass the full website gate; verify a preview and
deploy; then check live links and close both projects. Select the host and confirm
domain/DNS access during that session. Do not claim the site is deployed beforehand.

On 2026-10-18, the active `main` ruleset was verified with all five required CI
checks, strict up-to-date merging, pull requests and deletion/force-push protection.
Private reporting was independently verified enabled; the maintainer confirmed
publishing-settings and PyPI visual reviews. The active `v*` tag ruleset was also
verified: updates/deletion are restricted and creation of new tags remains
permitted. The human Windows usability review remains deferred, with synthetic
data and PowerShell commands in
`local-data/ragvidence-0.2.0-manual-check.zip` in the CLI checkout. That ignored ZIP
is not a public download. Sponsorship remains optional and unconfigured. M7 is
deferred; no additional capability or release is needed for this handoff.
