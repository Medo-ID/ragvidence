# Portable RAG diagnosis and technique comparison plan

Date: 2026-10-15. Status: M1–M3 implemented in development. The integrity foundation,
portable BM25, additional file loaders and portable configuration are available.
M4's portable techniques, span scoring, budgets and external imports are implemented
and tested, including two fingerprinted embedding models on fixed reviewed data.
M5 provides comparisons, bounded grids, paired intervals, frozen shortlists and
validated resume. M6 now implements metadata scopes, cosine MMR, bounded query
rewriting and exact-span compression through the shared portable pipeline.
M7 is deferred at the user's request. M8 release preparation is now authorized:
the 0.2.0 candidate is completely free under Apache-2.0, with consolidated Linux
evidence and cross-platform CI gates. Linux, Windows and macOS ARM64/Intel now
pass 395 tests plus installed wheel/source/optional-runtime and upgrade journeys.
Live index publication remains pending. No new release has been published. See
[implementation evidence](portable-implementation-evidence.md) for delivered scope.

## Feasibility and product contract

This direction is feasible using the existing Python CLI, native retrieval
strategies, provider adapters and self-contained report renderers. The product
layers include ordinary-file ingestion, unlabeled question handling, shared
application orchestration, exact context recording and automatic report creation.
The portable implementation covers BM25 over TXT/Markdown, HTML, document JSON/JSONL,
CSV and optional text PDFs; the original
workspace loader still serves the existing reviewed-data workflows.

The product promise is: **install once, diagnose a RAG technique on your own data,
and compare ready-made alternatives without implementing each experiment.**

The primary interface is `ragvi TECHNIQUE INPUT`, where INPUT is a supported local
file or folder. Users work from any directory without a Python project, framework,
manual workspace or configuration file. The tool prepares internal artifacts,
prints a terminal summary and saves shareable reports. Existing RAG system results
can optionally be imported as a baseline; users need not already have a RAG system.
The user decides which technique fits their project.

The [portable CLI specification](../portable-cli-design.md) owns exact command,
input, prompt and output behavior. This roadmap owns architecture, delivery order,
test contracts and release gates. Keep these two documents consistent.

Examples of the target interface:

```bash
ragvi bm25 ./manual.txt
ragvi semantic ./docs --query "How do I reset the device?"
ragvi hybrid ./manual.pdf --questions ./questions.jsonl --format html --format json
ragvi compare-data ./docs --techniques bm25,semantic,hybrid --questions ./questions.jsonl
```

Default exports are a terminal summary and self-contained HTML. Repeatable
`--format` selects HTML, JSON and/or Markdown. `--output` controls the report root;
source files remain unchanged. Models, indexes and internal snapshots are managed
automatically. Flags support scripts; optional prompts support interactive use.

## Evaluation levels and practical limits

| Available input | Honest result |
| --- | --- |
| Sources only | `ingestion_only`: extraction, structure and chunk diagnostics; no retrieval-quality score |
| Sources and questions | `retrieval_inspection`: actual ranked passages, traces, timing and context usage; no invented relevance score |
| Sources, questions and reviewed evidence | `reviewed_evaluation`: evidence metrics, failure cases and scored comparisons |
| Optional answers and suitable references/judgments | Separate answer/citation/abstention evaluation |

A file alone cannot define what a retriever should find. Accept questions through
repeatable `--query`, a `--questions` file or a terminal prompt. Do not force users
to author evidence labels just to inspect a technique. Optional generated questions
or judgments have distinct recorded provenance and provisional status until reviewed.

Scope the first release to text evidence: TXT/Markdown first, then HTML, document
JSON/JSONL, CSV and optional text-bearing PDFs; folders contain supported formats.
Scans/OCR, multimodal data, DOCX/spreadsheets, URLs and databases remain later work.
Extraction quality and supported languages must be stated and tested; successful
file decoding alone is not proof of faithful tables/layout or multilingual retrieval.
BM25 runs offline. Local semantic models may require a first download; remote
providers require explicit configuration. Portability is tested on each advertised
operating system and does not imply every file type or unbounded corpus scale.

Users save implementation and investigation time. An investigation is useful even
when no alternative beats the current technique. Tests establish correct supported
behavior; evaluations describe observed results on the user's corpus. The product
does not modify, deploy or automatically optimize the user's RAG application.

## Baseline audit before this implementation

The audit covered the CLI, domain models, data loading, native and imported runs,
all retrieval strategies, representation/chunking, provider adapters, generation,
metrics/evaluation, comparison/diagnosis, report payload/renderers/template,
health/workspace/installation verification, tests, packaging and CI/release files.

Baseline commands:

```bash
.venv/bin/pytest --cov=ragvidence --cov-report=term-missing
.venv/bin/ruff check src tests
```

Observed: **90 tests pass; 81% statement coverage; lint passes**. Most tests live
under `tests/unit`, including some CLI integration checks. The metrics and evaluator
have 100% statement coverage, but that does not test missing validation behavior.
Generation is at 33%, remote providers at 65%, and CLI commands at 58%.

| Area | Existing foundation | Required correction or extension |
| --- | --- | --- |
| `data.py`, `models.py` | Strict schemas and evidence reference checks | Canonical identity, artifact versions, exact source spans and finite numeric values |
| `runner.py` | Native strategy composition and reproducibility metadata | Separate configuration resolution, provider construction, execution, context assembly and recording |
| `strategies/`, `providers/` | Retrieval and embedding protocols, reusable RRF | Shared contracts, stronger provider validation, independent indexing/cache identity |
| `evaluation/evaluator.py` | Pure evidence metrics and per-question output | Validate the run against its snapshot before trusting hits; summarize splits and all metrics |
| `comparison.py` | Dataset/depth checks and regression classification | Typed inputs, budget-aware comparability, slices, uncertainty and resource trade-offs |
| `generation.py` | Optional user-owned models | Consume exact recorded context and expose typed answer/judgment artifacts |
| `reporting/` | Shared payload and escaped, self-contained HTML | Compute evidence differences and decisions once; render the same facts in all formats |
| CLI / CI / verification | Useful local workflow and package builds | Shared application services, installation tests and explicit capability verification |

Concrete issues found:

1. `canonical_dataset_bytes()` sorts object keys but leaves set-derived arrays
   unordered. On the unchanged bundled dataset, `PYTHONHASHSEED=1` and `=2` produced
   different SHA-256 digests. This breaks cross-process reproducibility.
2. Evaluation loads current questions but does not compare the run's dataset hash
   with the current dataset or validate every recorded hit against the sources.
   It trusts `hit.evidence_ids`; duplicate/missing query records are not rejected
   at this boundary. Comparison also collapses duplicate question IDs into dicts.
3. Numeric hit scores accept NaN. Embedding validation checks shape but does not
   consistently reject nonfinite/zero vectors or malformed response indexes.
4. Semantic cache identity currently contains model name and text only, allowing
   collisions across providers or encoding configurations using the same name.
5. Source-level evidence labels cannot establish which independently returned or
   compressed passages actually contain a fact.
6. Generation reloads full sources; runs do not preserve exact final context.
   This would invalidate future chunk-only/compression answer comparisons.
7. Evaluation summary pools dev and heldout and summarizes sufficiency only.
   Query latency exists in runs but is not carried through into comparison metrics.
8. `candidate_k` serves several different stages. Nested RRF metadata can overwrite
   earlier stage contributions. Child IDs depend on corpus iteration position.
9. CLI workflows duplicate orchestration and JSON writing. HTML recomputes found,
   missing and changed evidence; report limitations always describe teaching data.
10. Import timing uses zero plus a warning; future statistics must treat it as
    unavailable. The importer truncates hits before validating the unused tail.
    Its input types and nonfinite numbers need consistent validation.

## Target architecture

Use one application path for every technique:

```text
CLI request and preflight
  → source discovery / format loaders
  → immutable corpus snapshot + questions + optional reviewed labels
  → resolved technique preset / experiment request
  → query transformation / retrieval / selection stages
  → exact final context + stage traces
  → diagnostics / optional reviewed evaluation
  → shared report model
  → terminal summary + requested exports + internal artifacts
```

| Boundary | Single responsibility |
| --- | --- |
| `ingestion/` | Deterministic discovery, format extraction, metadata and location mapping |
| Domain contracts | Separate corpus, exploratory questions, reviewed references, run/context, evaluation and report values |
| Validation / provenance | Canonical identities, spans, compatible inputs and artifact integrity |
| Configuration / pipeline building | Resolve settings once and construct explicit technique stages |
| Retrieval / transforms / context | Rank candidates, transform questions and select actual returned passages |
| `providers/` | Embedding, cross-encoder, chat, tokenizer and optional judge adapters |
| `evaluation/` and diagnosis | Pure metrics, evidence resolution, aggregation and evidence-linked explanations |
| Experiment services | One-technique runs, imported baselines and multi-technique orchestration |
| Artifact storage / cache | Atomic versioned writes, safe paths, snapshots and compatible cache reuse |
| Report view model / renderers | Compute facts once; render identical facts in each output format |
| CLI | Parse options, collect optional answers and present progress/results |

DRY and decoupling rules:

- Reuse existing BM25, semantic, RRF, parent-child and reranking implementations.
  Refactor their boundaries instead of rewriting working algorithms.
- Technique commands are thin adapters backed by one capability catalog and shared
  request/execution service. Do not copy an entire pipeline into each command.
- Define an exploratory question contract without required gold labels. Reviewed
  evidence is separate optional evaluation input. Do not mark unknown questions
  unanswerable or invent evidence to satisfy current `QuestionCase` validation.
- Keep searchable representations, original extracted text and returned context
  distinct. Query/retrieval stages never receive gold evidence or reference answers.
- Resolve provider/configuration once; inject small interfaces and deterministic
  clocks/seeds where needed. Prefer functions and small protocols to a plugin framework.
- Use one canonical serializer, evidence resolver, context assembler, artifact
  validator, summarizer and report facts model. Templates only display facts.
- Ordinary-file and legacy workspace inputs normalize into the same contracts.
  The new workflow must not create parallel scoring or report implementations.
- Preserve unknown fields of external-system provenance as unknown; reproducing a
  named technique internally does not prove an exact match to the user's system.
- Every milestone includes its callers, docs, fixtures and installed-command checks.
  Integration is part of delivery, not a cleanup after features have accumulated.

## Delivery milestones

### M1 — Integrity foundations and shared request contracts

Scope:

- Fix set canonicalization and define versioned corpus, question/reference,
  representation, configuration and context identities. Meaningful ordering stays
  explicit; changing an embedding model does not change the gold corpus identity.
- Add typed exploratory questions, optional reviewed references, execution status
  and evaluation level. Version old artifacts with explicit migration/read adapters.
  Legacy artifacts without adequate provenance remain unverified until rerun or
  valid migration; never claim new proof was recorded in an old run.
- Centralize run validation: snapshot match, exact declared question subset, source
  mappings, unique result IDs, contiguous ranks, depth limits and finite values.
  Validate full external records before truncation; do not trust supplied evidence.
- Harden embedding cardinality, indexes, shape, finite/nonzero vectors and encoder
  compatibility. Cache identity includes provider, model/revision where available,
  encoding settings, dimensions and text. Validate corrupt/stale cache behavior.
- Centralize safe output names and atomic no-overwrite writes. Extract reusable
  configuration/pipeline construction from CLI and runner while preserving callers.

Gate: cross-process/hash-seed reproducibility; correct empty/unlabeled contracts;
rejection of tampered evidence, wrong snapshots, missing/duplicate questions, NaN,
bad ranks/vectors and cache collisions. Existing tests pass through shared services.

### M2 — First usable portable command: TXT/Markdown → BM25 → report

Scope:

- Implement the loader contract and deterministic TXT/Markdown discovery for files
  and folders. Preserve immutable original/extracted text, file hashes, line/heading
  locations, exact character offsets and extraction warnings.
- Build reusable passage records with stable source/offset/config-based IDs.
  Default chunking and units are explicit; source documents do not become single
  giant search results. Reviewable spans are present before full evidence scoring.
- Implement `ragvi bm25 INPUT` with `--query`, `--questions`, `--no-input`, repeatable
  `--format`, `--output` and `--cache-dir`. Ask for questions only when needed on a
  terminal. A noninteractive source-only run never waits for input.
- Generate the internal snapshot and run automatically. Route through one
  application service with stage traces, exact final context and null unavailable
  measurements; do not require `init`, manual JSONL conversion or project files.
- Adapt the report contract/renderers for ingestion-only and retrieval inspection,
  alongside existing reviewed reports. Print useful findings and paths; save HTML
  by default and support explicit JSON/Markdown exports. Unknown metrics remain N/A.
- Preflight dependencies/output access; keep sources read-only; exclude questions,
  reports and caches from folder inputs. No automatic browser launch.

Gate: install the built wheel in an isolated tool environment, invoke it from an
unrelated directory against TXT/Markdown, provide a question, and verify terminal
and HTML evidence. Test source-only status, query files, scripted use, relative and
absolute paths, Unicode/spaces, output overrides and no-overwrite. The report
remains readable after cache removal. This milestone delivers a usable product slice.

### M3 — More input formats and portable configuration

Delivered in development. See [verification evidence](portable-implementation-evidence.md)
and [current usage](../portable-file-usage.md) for tested formats and extraction limits.

Scope:

- Add HTML, document JSON/JSONL and CSV loaders; text-bearing PDF extraction is an
  optional extra. Preserve page/record/row/heading locations and extraction identity.
- Select a single unambiguous text field/column or require an explicit option or
  terminal selection. Keep metadata without flattening arbitrary structured values
  or importing reference answers into searchable text. Distinguish source schemas,
  question files and existing RAGvidence artifacts explicitly.
- Add mixed-folder loading, include/exclude and file/byte limits, deterministic
  ordering, documented symlink behavior, and visible skipped/failed extraction counts.
- Resolve settings as CLI flags → environment variables → explicit config file →
  user-level config → built-in defaults. Never implicitly read an unrelated current
  directory's `.env`; allow explicit `--env-file`. Secrets stay out of artifacts.
- Support writable output/cache overrides for read-only inputs and different host
  platforms. Do not silently download parsers or models to make a missing extra pass.

Gate: independent extraction/location fixtures for every advertised format; bad
encoding, ambiguous fields, malformed records, empty/encrypted/scanned PDF behavior,
unsupported files, resource limits, mixed folders and settings precedence. Compare
representative extracted text against reviewed originals, including table/layout limits.

### M4 — Existing techniques, exact evidence and optional existing-system baselines

Implementation status: core execution path is in development, including all existing
technique entry points, original-span union scoring, stage limits/traces, exact local
tokenizer budgets and verified external spans/ID proxies. See [usage](../portable-techniques.md)
and [recorded model compatibility](../../verification/portable-m4/model-check.json).
The T11 compatibility check runs BGE small and MiniLM on the same eight-source,
twelve-question reviewed corpus. Evidence records successes, failures and ties, with
model/tokenizer file fingerprints. These bounded fixtures do not establish general
production quality; broader domain/model/OS coverage remains part of release work.

Scope:

- Expose semantic, hybrid, reranking, parent-child, contextual indexing and supplied
  multi-query presets through the same portable request path. Map exact commands,
  base retrievers, parameters and prerequisites in the capability catalog. Chunking
  and overlap are shared settings, not duplicate retrieval pipelines.
- Support independent passages versus expanded parents. Stable reviewed evidence
  items anchor to one or more original text spans; complete union coverage earns
  evidence credit. Duplicate overlap never adds credit, and prefixes never become gold.
- Add reviewed-question/evidence input and reference validation. Make source
  locations visible so users can author/review expected evidence without manually
  creating internal workspaces. Do not require a label-review application.
- Store exact returned text, source spans, order, context identity and every stage's
  scores/timing. Split ambiguous `candidate_k` into documented stage limits; retain
  legacy adapters and preserve nested fusion contributions.
- Add identified tokenizer/counting adapters and context budgets. Distinguish exact
  counts from estimates; count complete rendered requests for optional generation.
  Selection initially keeps ranked whole passages that fit, skipping oversized ones.
  Any truncation must update spans and evidence credit.
- Import current-system results as an optional participant, including exact context
  and source mappings where available. Cross-chunk mapping uses the frozen originals.
  ID-only imports cannot claim the same diagnostic depth as exact-context imports.

Gate: contracts for T01–T12; genuine model compatibility tests for affected model
adapters; child failure versus parent success; boundary evidence union; duplicate
credit prevention; exact context parity; budget behavior and source mapping. The
same reviewed evidence is scored identically for equivalent native/imported context.

### M5 — One-command comparison and decision reports

Implemented in development. See [current usage](../portable-comparisons.md) and
[recorded model suite evidence](../../verification/portable-m5/model-check.json).
Limits remain explicit: local heldout ledgers, user-supplied usage/pricing,
unknown model-cache warmth, no nDCG without graded gains, and Linux-only installed
execution evidence. No universal quality winner or release publication is claimed.

Scope:

- Add `ragvi compare-data INPUT --techniques ...`; support optional imported baseline,
  ready-made diagnostic presets and advanced suite JSON. Load/freeze sources and
  questions once, then execute all selected techniques against that snapshot.
- Make each configuration/dependency visible; bound configuration count and model
  calls. Reuse only compatible indexes/embeddings. Resume validated completed runs,
  record failures and never silently overwrite. Record cold/warm timings separately.
- Support controlled grids for chunks, overlap, model, candidates, final depth/budget,
  hybrid weights and rerankers. Explore on dev and freeze a user shortlist before
  heldout evaluation; record heldout reuse. No automatic optimization requirement.
- Declare comparison policy: fixed depth, fixed exact token budget, or descriptive
  trade-offs. Do not treat equal k as equal context. Unlabeled comparisons show actual
  ranked contexts and resource differences without declaring a quality winner.
- Aggregate sufficiency, evidence coverage, MRR and precision with denominators;
  keep dev/heldout and predeclared slices separate. Add nDCG only when reviewed
  relevance gains support it. Include sample counts and per-question changes.
- Add paired seeded intervals over questions, grouping related questions when
  appropriate; repeated trials do not create independent questions. State small
  sample behavior and label broad grid exploration accordingly.
- Carry available latency, tokens and usage/cost into comparisons. Missing imported
  timings remain null. Costs need supplied pricing identity; estimates are labeled.
- Explain supported diagnosis stages with actual cases; distinguish hypotheses and
  unavailable traces. Compute evidence gained/lost/missing once for all renderers.
  Present strengths, weaknesses, ties and optional user-criterion matches. Keeping
  the existing technique is a valid outcome; the user decides.

Gate: own files → optional imported baseline → built-in techniques → one report,
without Python code. Test shared snapshots, question-file exclusion, cache isolation,
resume/failure, comparison compatibility, hand-calculated summaries/intervals, empty
slices, timing gaps, ties and no-better-alternative cases. All export facts reconcile.
**M1–M5 define the first complete portable diagnosis/comparison release scope.**

### M6 — Extend the catalog with prioritized techniques

Status: implemented in development. See the implementation evidence and
[advanced technique guide](../portable-advanced-techniques.md). M7 remains deferred;
routine milestone tests do not constitute the consolidated M8 release gate.

Implement through the same stages, loaders, artifacts and reports:

1. Metadata filters: typed equality/membership/range predicates with defined missing
   fields, applied before ranking and preserved through variants/parent expansion.
2. MMR: explicit embedding identity, diversity objective, lambda/candidate limits,
   deterministic ties, resource measurement and preserved selection provenance.
3. Automatic rewriting/multi-query: question-only model input, bounded calls/variants,
   explicit original-question policy, recorded prompt/model/query output and failure
   handling; reuse the shared RRF function.
4. Extractive compression: exact selected input spans, validated provenance, explicit
   order and budget behavior; recalculate evidence after removal. Start deterministic,
   then add an optional model span selector. Abstractive summaries remain deferred.

Gate: T13–T16 plus filters with hybrid/children/variants, reranking with MMR, parent
expansion with compression and final budget selection. A bad rewrite or removed
qualification appears as a diagnostic failure/regression, not an assumed improvement.

### M7 — Optional answer/citation evaluation

Scope:

- Accept imported answers or optionally generate from the exact recorded context.
  Bind answers to question/run/context and model/prompt identities. Keep this
  workflow optional and separate from retrieval technique diagnosis.
- Evaluate reference correctness/completeness, claim support, citation validity/
  support/coverage and abstention independently. Extend reviewed reference schemas
  as needed; arbitrary prose references are not automatically verified claim labels.
- Validate cited IDs deterministically. Optional semantic model judgments use a
  separate adapter, versioned rubric and retained structured output. Invalid or
  unavailable judging never becomes a pass or changes retrieval labels.
- Calibrate optional judges against reviewed cases; report agreement/error rates
  and distinguish estimates from reviewed evidence. Optional question drafts also
  retain provisional provenance and require review before becoming gold.

Gate: supported but incomplete answer, correct unsupported answer, irrelevant real
citation, nonexistent citation, uncited support, correct/unnecessary abstention,
malformed judge output, provider failure and wrong-context answers remain distinct.
**This optional milestone does not block the M1–M5 core release.**

### M8 — Consolidated capability and release verification

Global-install checks and documentation updates happen in every milestone. This
milestone consolidates release evidence for whichever scope is actually shipped.

- Verify the capability catalog has a positive case, negative case, runnable preset
  and CLI-to-report fixture for every advertised technique/loader. Report supported,
  missing-dependency, not-run and failed statuses distinctly.
- Split mixed tests by responsibility; share small dataset builders/fakes and use
  independently computed expectations. Core CI blocks accidental network access.
  Separate pinned local-model tests and optional bounded credentialed provider jobs;
  skipped model jobs never count as passing integrations.
- Install wheel/source distributions into clean environments. Test advertised OS
  targets, unrelated directories, relative/absolute Unicode paths, source-only and
  query/graded modes, defaults/prompts/flags, exports, read-only inputs and cache deletion.
- Update CLI help, README, input schemas, examples, metric definitions, technique
  coverage, privacy/provider docs, changelog and release instructions together. Keep
  planned and shipped capabilities distinct and reconcile existing edition claims.
- Verify packaged fixtures, templates and catalog; exclude credentials, customer
  data, caches and internal maintainer planning files. Do not publish as part of
  implementation; prepare reviewable release artifacts under the existing process.

Release gate: all capabilities in the shipped scope pass their contract and
installed-user journey; relevant model integration evidence is recorded; report
facts reconcile; no known integrity or scoring defect remains. Statement/branch
coverage supplements these behavioral gates and is not itself a capability claim.

## Technique verification matrix

Every row needs a positive case, negative/adversarial case, valid configuration,
trace/provenance assertions and a CLI → run → evaluate → compare/report fixture.
Model-based rows additionally need a pinned-model compatibility test. A quality
benchmark must include a neutral or regression case rather than assuming every
technique improves every question.

| ID / technique | Deterministic contract to prove | Model or quality check |
| --- | --- | --- |
| T01 BM25 | Reviewed lexical fixture; identifier/version tokens; empty/OOV/tied results; correct depth/evidence | Lexical identifiers versus paraphrases on reviewed questions |
| T02 Dense cosine | Independent cosine oracle; query/document encoding; normalization; stable ties; invalid vectors rejected | Pinned local embeddings retrieve reviewed paraphrases; mismatch fails |
| T03 Hybrid RRF | Hand-calculated weighted ranks; absent lists; duplicate suppression; candidate limits; all branch traces retained | Complementary lexical/semantic cases, including regressions |
| T04 Cross-encoder | Only candidates reorder; original question used; finite/cardinality checks; prior scores retained; truncation disclosed | Pinned model smoke and reviewed quality comparison |
| T05 Recursive splitting | Exact offsets; bounded sizes; full text coverage; deterministic IDs; Unicode and empty-boundary cases | Evidence crossing a separator and fallback hard boundary |
| T06 Markdown splitting | Declared ATX heading/fence semantics; hierarchy/offsets; long-section fallback; unsupported syntax stated | Structured manual versus flat prose |
| T07 Overlap | Configured overlap within sections; no missing characters; union evidence counted once | Boundary evidence recovered with measured extra context/indexing |
| T08 Parent-child | Child-to-parent mapping; best-child order; deduplication; explicit full-parent context; limited candidate behavior | Child insufficient but parent sufficient; extra-context trade-off |
| T09 Context enrichment | Authentic headings/reviewed prefixes; original text unchanged; no gold-label access; prefixes never earn evidence credit | Relevant, neutral and misleading prefix cases |
| T10 Multi-query | Original query policy; bounded unique variants; shared filters; RRF math; stable provenance and failure policy | Helpful paraphrase plus noisy variants that can regress |
| T11 Embedding comparisons | Separate model/provider/revision/encoding cache identities; shared corpus/labels and policy | At least two pinned compatible model configurations on one corpus |
| T12 Independent chunks | Gold spans independent of chunk IDs; span union; partial evidence fails; budget truncation reflected | Same source/questions, chunk size/overlap ablation |
| T13 Metadata filters | Predicate truth tables; missing/type-mismatched fields; applied before cutoff; no filtered-out context or parent leakage | Version/product/source scope with tempting excluded distractors |
| T14 MMR | Hand-calculated relevance/diversity objective; lambda endpoints; ties; uniqueness and pool limits | Duplicate-heavy candidates versus complementary evidence |
| T15 Automatic rewrite | Question-only interface; configured original inclusion; bounded calls/variants; invalid/failure policy; exact transformed query logged | Helpful and intent-drifting rewrites, judged on original question |
| T16 Extractive compression | Output is exact input spans; provenance validates; removed facts lose credit; budget/order/empty output defined | Keep answer plus qualifications; expose removal-induced regression |

## Shared fixtures and testing layers

Retain the existing teaching tutorial as a legacy regression fixture. Add ordinary
TXT/Markdown, HTML, CSV, JSON/JSONL and text-PDF fixture files plus reviewed extracted
text, source locations and checksums. Evaluation fixtures add evidence spans,
question splits/tags/source groups and reference claims without embedding labels in
the searchable source. Cover identifiers, paraphrases, multiple facts, near duplicates,
versions, context-dependent sections, boundaries, large passages, excluded distractors,
unsupported questions, Unicode and extraction failures.

Use four layers:

1. Unit/invariant cases: pure algorithms, schemas, loaders, spans, serializers,
   budgets and seeded randomized checks against independent expectations.
2. Contract/integration cases: shared stage/provider/loader contracts, malformed
   output, local HTTP adapter fixtures, caches, storage and declared combinations.
3. CLI/installation cases: ordinary files/folders, terminal/no-input behavior,
   unlabeled/reviewed inputs, automatic artifacts, all export modes, legacy reads,
   error/resume paths and commands outside the installation directory.
4. Model compatibility/reviewed evaluations: pinned local models and optional
   bounded remote providers, with saved identities and actual quality observations.

For each advertised technique retain implementation version, capability scope,
fixture IDs, contract outcome, model integration status and CLI workflow result.
User reports additionally bind findings to corpus/question/evidence identities,
configuration, context and measurements. Test outcomes establish support; user-data
comparisons supply project-specific diagnostic evidence.

## Delivery order and acceptance

Order: **M1 → M2 → M3 → M4 → M5**, followed by **M6** catalog expansion and optional
**M7** answer evaluation. Apply **M8** release gates to each actual delivered scope.
The existing codebase audit and 16 technique contracts remain part of this plan.

Start each milestone with its failing behavioral cases, implement through shared
boundaries, update existing callers/docs and run focused plus full offline checks.
Run model checks when affected adapters/techniques warrant them. Keep reviewable
milestones and evidence records; no feature is complete until its whole command,
artifact and report path is cohesive.

The essential acceptance scenario is a globally installed `ragvi` invoked from a
user-chosen directory against their ordinary data, obtaining questions as needed,
running a technique or comparison and producing an understandable shareable report.
The user writes neither retrieval implementations nor evaluation plumbing.
