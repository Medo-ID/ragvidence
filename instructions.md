# Website update handoff: RAGvidence 0.2.0

Prepared 2026-10-16 in the CLI repository. Execute website changes later in
`../ragvidence-web`, following that repository's own instructions. This file is
an implementation brief, not a claim that the new CLI is already published or
that website assets are now Apache-licensed. No website files were changed here.

## Product and business direction

RAGvidence is a portable CLI for **diagnosing and comparing RAG retrieval techniques
on the user's own data**, validating evidence and producing shareable reports.
It saves users from implementing each technique/framework experiment themselves.
The decision is theirs, for their own RAG system. Do not promise automatic changes
to production systems, universal retrieval improvements or correct generated answers.

From 0.2.0 the entire CLI is **free, Apache-2.0**, with every included feature
available without accounts, activation, payment, seats or a subscription. Remove
Free/Plus cards, locked capabilities, checkout/entitlement/activation flows and
future paid-feature promises throughout pages, docs, metadata, structured data,
assets and tests. Replace them with one free installation/download path.

Add an optional “Sponsor” or “Support the project” button. Users choose whether to
contribute and the amount. Donations do not unlock features or buy a support SLA.
The maintainer has not supplied a payment destination: obtain the chosen external
sponsorship/donation URL before wiring a real button. Do not invent one, implement
an unrequested payment backend, or make charitable/tax-deductibility claims.
No donation requirement belongs in the CLI installation path.

Apache-2.0 applies to the new CLI release. Keep third-party/font/model notices.
Historical 0.1.0 was published under earlier proprietary terms: do not silently
replace that old license download with the new license. Label or archive old
release docs. Website code, branding, images and other assets do not inherit a
license from this change; assess them separately with the maintainer.

## Source of truth and publication status

Before editing public claims, read these from the CLI repository:

- `pyproject.toml`, `src/ragvidence/__init__.py`, `uv.lock`: candidate version 0.2.0,
  Python **3.12 only** (`>=3.12,<3.13`), console command `ragvi`, extras `pdf`, `semantic`.
- `src/ragvidence/capabilities.py`, `ragvi techniques --format json`, installed
  command help: actual presets, options and prerequisites.
- README, CHANGELOG, `docs/portable-file-usage.md`, `docs/portable-techniques.md`,
  `docs/portable-comparisons.md`, `docs/portable-advanced-techniques.md`,
  `docs/rag-technique-coverage.md`: actual scope, schemas and limitations.
- `verification/portable-m8/`: actual Linux test/install/model/upgrade outcomes;
  `.github/workflows/verify-release.yml` and the latest successful GitHub run:
  actual OS results. A configured matrix is not evidence that its jobs passed.
- `LICENSE.md`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, `THIRD_PARTY_LICENSES.md`.

0.2.0 is prepared here, **not published by this session**. Verify live PyPI and
TestPyPI separately before promoting installation commands or downloadable files.
At preparation time the public PyPI release is 0.1.0 and lacks portable commands.
Do not tell users to install the old release and then run unavailable commands.
Match source commit, installed version, release notes, artifact SHA and demos.
Once 0.2.0 is published the main installation example can be:

```bash
uv tool install --python 3.12 "ragvidence==0.2.0"
ragvi --version
ragvi verify
```

Optional runtimes: `"ragvidence[pdf,semantic]==0.2.0"`. A globally installed
`ragvi` runs from any ordinary data directory; users need no source checkout,
Python project, workspace, database or framework setup for portable commands.
Provide appropriate Windows/PowerShell and macOS/Linux instructions without
claiming every OS/Python version works. `uv` can manage Python 3.12.

## Capabilities that can be described

| Area | Implemented scope |
| --- | --- |
| Input | Local UTF-8 TXT/Markdown, visible-text HTML, document JSON/JSONL, CSV; text-bearing PDFs with `pdf` extra; mixed folders |
| Techniques | BM25, dense cosine, weighted hybrid RRF, optional local cross-encoder reranking, parent-child, heading context, supplied reviewed context prefixes, supplied multi-query fusion |
| Additional stages | Typed metadata predicates, cosine MMR, bounded model query rewrite/auto-multi-query, exact extractive compression (deterministic sentences or model-selected offsets) |
| Configuration | Recursive/ATX Markdown splitting, overlap, stage depths, context budgets, explicit local tokenizer where selected, embedding/provider comparisons |
| Existing systems | Import actual original-span results, or explicitly limited registered-unit ID proxies; optional existing-system comparison baseline |
| Comparisons | Shared frozen inputs/labels, bounded suites/grids, paired intervals, dev shortlists before heldout, local heldout-reuse disclosure, partial failures and validated resume |
| Outputs | Terminal summary and self-contained HTML by default; repeatable HTML/JSON/Markdown formats and custom output root |
| Reproducibility | Frozen data, original span offsets, exact final contexts, hashes, stage candidates/scores/timings, transformations and explicit missing-resource values |
| Existing workflow | Bundled fictional tutorial, workspace validation/benchmark/import/evaluate/compare/report/recovery; optional answer generation for inspection only |

Do not advertise a catalog count as a count of distinct algorithms. There are 14
preset/import entries; 16 planned technique contracts also include modifiers and
ablation dimensions. Explain the actual experiments instead of inflating the count.

Suggested examples, checked against installed command help:

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
ragvi bm25 ./docs --questions ./questions.txt --format html --format json
ragvi compare-data ./docs --questions ./questions.txt --techniques bm25,parent-child
ragvi techniques
```

`--output` selects the report root, default `ragvi-reports/`. Queries can come
from flags, a question file or an interactive prompt. Avoid promising a format
selection prompt unless actual installed behavior is verified; format flags work.
No file is automatically a scored benchmark:

| Input available | Honest result |
| --- | --- |
| Sources only | Ingestion/chunk diagnostics, no retrieval quality score |
| Sources + questions | Ranked retrieval/context inspection, no invented relevance metrics or quality winner |
| Reviewed original-span evidence too | Evidence sufficiency/coverage, first rank, reciprocal rank, precision and scored gains/regressions; disclosed denominators |

Quality claims apply to the user's reviewed questions and corpus. Small synthetic
checks establish execution/contracts, not general superiority. Imported ID-only
proxies have narrower evidence scope. Missing timing, token usage and costs stay
unavailable; supplied usage/pricing is an estimate, not an actual bill.

## Local model wording

It is accurate to say: **“Supports local embedding models and user-owned Ollama
models for query rewriting and extractive compression.”** FastEmbed runs selected
ONNX embeddings/rerankers locally after a first model download. Ollama embedding
and chat adapters and user-configured OpenAI-compatible endpoints are included.
An OpenAI-compatible endpoint can be local or remote; do not imply all are local.

BM25 and deterministic sentence compression need no LLM. RAGvidence does not ship
or install Ollama/a bundled chat model and does not provide API credits or hosting.
Model license, first download, output-contract compliance, language quality,
CPU/RAM/GPU needs and actual hardware remain user/provider dependent. Avoid “works
with any LLM”, “all models tested”, “zero network under all configurations”, or
universal GPU-free/hardware performance claims.

Linux compatibility evidence includes pinned BGE-small, MiniLM embeddings and a
Xenova MiniLM reranker, plus bounded local Qwen3:8b transformation checks. Retain
actual quality failures: a structurally valid compression can remove all required
evidence. Check the current evidence file before quoting any specific result.
Mutable model names are not immutable revision guarantees for every run.

## Limits and truthful claims

- M7 answer correctness, citation correctness, abstention evaluation and calibrated
  LLM judges are deferred and **not included**. Legacy `generate` is inspection.
- No HyDE, multi-hop/agentic/self-reflective RAG, graph RAG, learned sparse search,
  multi-vector/late interaction or production retriever optimization is implemented.
  Check the coverage guide for further gaps; do not convert roadmap items into claims.
- No OCR/scanned-PDF, DOCX/spreadsheet/image/audio ingestion, URL crawler, database
  connector, hosted vector database or production RAG deployment service.
- Text extraction does not establish faithful visual tables/columns/layout.
  Resource limits do not imply unlimited datasets or a security sandbox.
- CLI CI targets Linux x64, Windows x64, Mac ARM64 and Mac Intel on Python 3.12.
  The preparation session ran Linux locally; GitHub run 38921470479 subsequently
  passed all four targets with 395 tests each, installed-package and upgrade journeys.
  Retained per-platform evidence is under `verification/portable-m8/github/38921470479`. Do not claim every OS/architecture.
- Reviewed labels are excluded from retrieval/transformation prompts. Remote
  providers receive the required questions/source text for the selected operation.
  First-time model downloads can contact upstream services. Do not make blanket
  telemetry/privacy promises for all third-party runtimes/providers.
- Reports and frozen artifacts may contain **full passages, questions, prompts and
  model output**, not just summaries. Explain reviewing/redacting before sharing.
  HTML is escaped and self-contained with embedded fonts and no remote assets.

## Website acceptance

Audit landing page, docs, install snippets, FAQs, navigation, metadata/OpenGraph,
structured data, license/download endpoints, videos/screenshots and sample reports.
Regenerate demos from the exact release and synthetic data; do not manually alter
scores, omit regressions or reuse old CLI output for new claims. Validate links
and examples against installed help. Keep any old-version docs clearly labeled.
Update existing tests that enforce Free/Plus messaging; add meaningful checks for
one free path, working optional sponsor link, actual supported formats and no
unsupported capabilities. Do not add rating collection or a payment system unless
asked. A voluntary sponsor button does not imply a review/rating feature exists.

Use that repository's build, lint, accessibility and browser checks. Confirm the
sample HTML report opens offline and on a narrow screen. Deploy only as separately
authorized in the website session; this handoff does not deploy anything.


## Public open-source transition

The maintainer made `Medo-ID/ragvidence` public during M8. The public-transition
follow-up should review all history, branches,
release attachments, Actions logs/artifacts and contribution rights for public
exposure. Private repositories can also run these OS checks. The maintainer authorized a
temporary verification branch; its push triggered the successful public CI run.
The branch is removed after testing, and the verified M8 changes are committed on
main as Medo-ID before the next release-preparation phase. This handoff does not
authorize deployment or invent a sponsorship destination.

Preserve the historical v0.1.0 tag and immutable PyPI artifacts, and describe
0.2.0 as the new Apache-2.0 release. Before announcing, add contributor setup,
meaningful test requirements, issue/PR guidance and a maintainer support/security
route. Link to Source / Contribute / Star once the repository is actually public.
Use `.github/FUNDING.yml` plus the website sponsor button only after the maintainer
chooses a working sponsorship/donation destination. Keep installation independent
of payment. See the internal `docs/maintainer/open-source-transition.md` plan.


## Latest release-preparation decisions

M8 is committed and pushed on main as `16d2557` (Medo-ID). The temporary
verification branch/worktree were removed; no PR was opened. Run 38921470479
passed all four OS targets with 395 tests each and installed-package/upgrade checks.
The owner confirmed the repository is public. Public contributor guidance and
issue/PR templates are prepared before the version-tagged release. The shared
release gate passed locally for this public-release preparation; raw outcomes
are retained in `verification/public-release/`. Publication is still pending.

The owner explicitly **deferred sponsorship setup** and requested setup guidance.
Do not display an active Sponsor/Donate button or add a Funding metadata URL until
an approved working destination exists. GitHub Sponsors offers custom amounts;
see docs/maintainer/sponsorship.md for the setup steps. Donations remain optional
and all included CLI features remain free. Website changes are still separate.
