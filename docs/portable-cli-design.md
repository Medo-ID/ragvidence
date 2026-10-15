# Portable file and folder CLI design

Status: M1–M3 are implemented in the development source: portable BM25 over TXT,
Markdown, HTML, document JSON/JSONL, CSV and optional text PDFs, with questions,
automatic passages, portable configuration and HTML/JSON/Markdown reports. It is
not yet published to PyPI. Other direct technique commands below remain proposed. See
[current usage](portable-file-usage.md) for the implemented command.

This specifies
the primary workflow of the [architecture and delivery plan](maintainer/rag-evaluation-roadmap.md).
The roadmap owns delivery order and verification; this document owns interface
behavior. Both describe the same portable product.

## User contract

Install RAGvidence once as an isolated global command. From any directory, run a
technique on a supported local file or folder. No project setup, framework, manual
workspace or source JSONL conversion is required for the normal workflow.

Proposed examples:

```bash
ragvi bm25 ./manual.txt
ragvi semantic ./docs --query "How do I reset the device?"
ragvi hybrid ./manual.pdf --questions ./questions.jsonl
ragvi parent-child ./docs --questions ./questions.jsonl --format html --format json
ragvi bm25 ./articles.csv --text-column body --format markdown --output ./results
ragvi compare-data ./docs --techniques bm25,semantic,hybrid --questions ./questions.jsonl
```

### Technique catalog and common options

The initial direct commands cover the existing native implementations. `bm25`,
`semantic` and `hybrid` choose base retrieval. `rerank` selects a cross-encoder
preset with an explicit/defaulted base retriever; `parent-child` searches smaller
passages and returns parents. `contextual` requires reviewed prefixes or a separately
enabled context preparation step; supplied `multi-query` requires query variants.
Show resolved settings and prerequisites, and fail preflight on missing required
inputs. A technique name alone must not silently substitute another technique.
Standalone passage retrieval, recursive/Markdown splitting, overlap and heading
enrichment are shared configuration options and are listed in the capability catalog.
Metadata filtering, MMR, automatic rewriting and extraction join the same catalog
only when their roadmap contracts pass.

| Common option | Contract |
| --- | --- |
| `--query TEXT` | Repeatable search questions; separate from gold labels |
| `--questions PATH` | A question file, excluded from discovered source inputs |
| `--format FORMAT` | Repeatable HTML/JSON/Markdown export selection; replaces default HTML set |
| `--output DIRECTORY` | Report root; a unique run subdirectory is created |
| `--cache-dir DIRECTORY` | Reusable model/index cache override |
| `--no-input` | Disable every prompt; available flags or source-only behavior apply |
| `--interactive` | Enable optional terminal choices; unavailable on nonterminal stdin |
| `--text-field`, `--text-column` | Explicit structured-document text selection |
| `--include`, `--exclude` | Source-discovery patterns |
| `--config`, `--env-file` | Explicit configuration inputs; never implicitly load a cwd `.env` |
| `--open` | Optional browser launch after successful report creation |

Model/provider settings, retrieval depth, splitting and budgets use shared options
where meaningful and are recorded in the run. Unsupported option combinations
fail before execution. A technique's unavailable parameters are not silently ignored.

Direct technique commands use one capability catalog and one application service.
Technique-specific options extend a shared validated configuration; they do not
duplicate discovery, extraction, questions, evaluation or report code. Model-based
techniques retain explicit dependency/provider requirements. Global installation
does not mean every model-backed operation works offline before model installation.

`compare-data` is the proposed name for the new raw-data comparison command, to
avoid ambiguity with existing `compare BASELINE INTERVENTION OUTPUT`. Existing
workspace/artifact commands remain available for advanced and legacy use. Do not
silently interpret an evaluation artifact as an ordinary source document.

## Initial input formats

Start with text evidence, using format-specific loaders behind one loader contract:

| Input | Proposed support | Source mapping and limits |
| --- | --- | --- |
| `.txt` | Core | UTF-8 text; line and character locations; clear decoding errors |
| `.md`, `.markdown` | Core | Original text, heading paths and original offsets |
| `.html`, `.htm` | Core | Visible text/headings; preserve extraction mapping; exclude scripts/styles; never fetch remote resources |
| `.json`, `.jsonl` | Core | Reviewed RAGvidence schemas or document records with an identified text field; retain record IDs and metadata |
| `.csv` | Core | One document per row; identified text column; retain row IDs and metadata |
| `.pdf` | Optional text-extraction extra | Text-bearing PDF pages; document/page locations; explicit extraction warnings |
| Directory | Core | Deterministically discover supported files recursively and show loaded/skipped counts |

For JSON/JSONL and CSV, recognize a single unambiguous `text`, `content` or `body`
field/column, show the selection, and allow `--text-field` or `--text-column`.
Ambiguity requires a terminal choice or an actionable noninteractive error. Never
flatten every value into searchable text or infer gold labels from arbitrary fields.
Preserve structured fields as metadata for filter experiments.

Scanned/image-only PDFs, OCR, DOCX, spreadsheets, images/audio/video, databases and
URLs are deferred inputs. An unsupported file gets a clear message; an empty or
unsuccessful PDF extraction must not masquerade as a successful retrieval test.
Text extraction success does not establish that tables/layout were preserved.

Folder loading has explicit include/exclude and file/byte limits, deterministic
ordering and a documented symlink policy (skip symlinks initially). Skip hidden
folders, `.git`, generated report/run directories and caches by default. Do not
execute files. Report unsupported/skipped/unreadable inputs; stop if no usable text
remains. Freeze the discovered corpus before writing any output.

Loader results contain extracted original text, source identity/location,
original-file and extracted-text hashes, extraction identity/settings and warnings.
Evidence spans anchor to the frozen extracted text, with page/record/line mappings
where available. Extraction settings belong to provenance and comparison identity.

## Questions and evaluation depth

A source file supplies knowledge; it does not supply the questions a retriever
must answer. Support progressive use without making reviewed labels an onboarding
requirement for every invocation:

| Available input | What the command reports |
| --- | --- |
| Sources only | `ingestion_only`: ingestion/structure/chunk diagnostics; retrieval quality is not scored |
| Sources plus a question/questions | `retrieval_inspection`: ranked passages, scores, traces, context size and timing; relevance quality remains unscored |
| Sources plus questions and reviewed evidence | `reviewed_evaluation`: retrieval evidence metrics and validated comparisons |
| Answers plus suitable reviewed references/judgments | Optional answer/citation/abstention evaluation under the architecture plan |

Accept repeatable `--query` flags and `--questions FILE`. Question JSONL may contain
ID/question only for exploration; graded question records require reviewed evidence
under the versioned evaluation schema. A plain UTF-8 question file may contain one
question per nonblank line; assign stable question IDs. Verify that question files
are excluded from source-folder discovery, even when located inside that folder.

If no question is supplied and stdin is a terminal, offer question entry or a
source-only diagnostic report. With redirected/noninteractive input, never block:
produce the source-only report with an explicit status and show how to supply
questions. `--no-input` always disables prompts. No prompt is needed when complete
flags are present. Separate execution errors from the report's unscored status.
Source-only diagnostics do not initialize retrieval models or require unused model
dependencies; reports state that the requested retrieval stage was not executed.

Optional model-generated question drafts require an explicitly chosen provider and
bounded request count. Record their provenance and whether expected evidence was
reviewed. Generated expected evidence is a provisional estimate, never silently
treated as human-reviewed gold. The first useful report requires no hosted model.

## Output behavior

- Always print a concise terminal summary: loaded/skipped sources, technique,
  question count, evaluation status, available findings, and saved report paths.
- Default to a self-contained HTML report plus the terminal summary. Keep a
  machine-readable run manifest internally regardless of selected export format.
- Accept repeatable `--format html`, `--format json`, and `--format markdown`.
  Explicit formats replace the default export set. A future PDF export is separate;
  browser print-to-PDF is available through the HTML report.
- `--interactive` can offer technique/output choices. Prompt only on a terminal;
  complete flags stay scriptable and never require interactive confirmation.
- Default output is `./ragvi-reports/<input-name>-<timestamp>-<run-id>/`. `--output`
  chooses the output root. Check writability early; refuse silent overwrites and
  print an actionable error when another output location is required.
- Keep input files unchanged. Use a platform-appropriate user cache for reusable
  models/index work, with `--cache-dir` override. Persist report provenance so a
  report remains inspectable after cache removal. No checkout-relative paths.
- Do not launch a browser by default. An explicit `--open` may do so when supported;
  a saved report remains usable if browser launching fails.
- Successful ingestion-only or retrieval-inspection execution exits successfully,
  with the evaluation level explicit in every report. Input/configuration/parser/
  provider/storage failures have nonzero exit status. A failed test against optional
  user-defined regression criteria has a separately documented nonzero status;
  ordinary low retrieval quality does not mean the command failed to execute.
- Settings resolve as flags → environment variables → explicit config → user-level
  config → defaults. Ordinary data directories do not implicitly supply credentials
  or remote-provider configuration via an unrelated `.env` file.
- Reports state source/query/evidence provenance, extraction limitations, actual
  technique settings and whether results are inspected, provisionally judged or
  scored against reviewed evidence. A source-only report does not rank techniques
  by retrieval quality.

## Delivery and tests

Deliver M1 integrity/shared contracts, then the M2 TXT/Markdown, BM25, questions
and report workflow. M3 extends loaders and portable configuration; M4 exposes
existing techniques and reviewed evidence/current-system imports; M5 adds raw-data
comparisons and decision reports. M6 extends techniques; M7 answer evaluation stays
optional. M8 release/portability checks apply throughout, beginning with M2's first
installed-command smoke test. Preserve advanced workspace APIs through shared services.

The first complete release target is M1–M5. Hosted generation, model judges and
future technique families are not prerequisites for the core portable investigation.

Required checks:

1. Each loader has expected text, metadata/location and error fixtures; transformed
   text and original-source mappings are independently checked.
2. Folder cases cover mixed formats, ordering, exclusions, question-file exclusion,
   symlinks, unreadable/unsupported/empty files and discovery limits.
3. Prompt/flag cases cover question entry, no-input execution, ambiguous structured
   fields, missing optional parser/model support and explicit provider selection.
4. Report cases cover defaults, each format and combined exports, output overrides,
   no-overwrite, unscored status, escaped hostile text and no automatic browser launch.
5. Install the built wheel globally in an isolated tool environment; run commands
   from an unrelated directory using relative/absolute paths, spaces and Unicode,
   read-only source folders and chosen writable report/cache locations.
6. One customer journey loads ordinary files, enters questions, runs a technique and
   opens a shareable report; another uses reviewed questions to compare techniques
   and an optional imported baseline. Neither requires user-written Python or a
   hand-assembled workspace.

The development `bm25` command implements the first raw-file workflow. Existing
benchmark/experiment commands continue to accept labeled workspaces. Broader raw-file
techniques, loaders, reviewed raw-file scoring and comparisons require later milestones.
