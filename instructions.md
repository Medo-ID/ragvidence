# Website handoff: RAGvidence 0.2.0

Use this brief in the separate `../ragvidence-web` session. Follow that repository's
AGENTS.md, README and maintenance guidance, and preserve existing uncommitted work.
The execution order is in
[the completion checklist](docs/maintainer/release-and-website-checklist.md).

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

The intended release is 0.2.0. Publication is pending at preparation time;
verify PyPI before saying it is available or regenerating production demos.
Record the live version/tag, release commit, artifact hashes and verification links
here after publication. Keep package, documentation, commands and demo provenance
aligned. Until the website is deployed, GitHub documentation links are usable.

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
Python 3.12. Run [38924470360](https://github.com/Medo-ID/ragvidence/actions/runs/38924470360)
passed on the public-preparation commit. Recheck CI for the final release commit;
a matrix definition alone is not proof of success. Real-model checks use identified
Linux configurations and do not establish inference compatibility on every OS.

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
