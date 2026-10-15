# Portable implementation evidence

Date: 2026-10-15. Scope: M1 integrity foundation, M2 portable BM25 and M3 additional
loaders/configuration in the development source. M1/M2 were committed as `4479a05`
before starting M3. No package has been published by this work.

## Delivered behavior

```bash
uv run ragvi bm25 docs/examples/device-manual.md --questions docs/examples/questions.txt
uv run ragvi bm25 ./manual.txt --query "Reset instructions" --format html --format json
```

- UTF-8 TXT/Markdown files and recursive folders work without `init` or manually
  prepared workspaces. Internal original-text snapshots and passages are automatic.
- Repeatable query flags, TXT/JSON/JSONL question files, terminal question entry,
  explicit output selection and no-input execution use the same application service.
- Terminal summary and HTML are the default; JSON and Markdown are available.
  Output directories are unique, originals remain unchanged and browsers only open
  when explicitly requested. Report paths are printed without inserted soft wraps.
- Sources-only mode is explicitly `ingestion_only`; supplied questions produce
  `retrieval_inspection`. Neither invents evidence/answer scores. Reviewed evaluation
  remains available through existing workspace commands.
- Original text/line/heading locations and exact returned passages are recorded.
  Actual input preparation settings are retained separately from retrieval settings.
- Questions/output roots, hidden paths, links and generated run directories are
  excluded from source discovery. File/count/byte limits and skipped inputs are explicit.

## M3 loaders and portable configuration

- Offline HTML, document JSON/JSONL and CSV use separate parser adapters feeding
  the same snapshot/chunk/retrieval/report service. Optional pypdf 6.20.1 extracts
  text pages without OCR. Missing extras explain how to install them; no automatic
  dependency installation occurs.
- Source units retain original page, record, JSONL line, CSV row/physical line range
  or HTML section/heading paths, file/text hashes and parser identity. The reports
  show these locations and the exact extracted passages. Physical CSV starts remain
  correct across blank lines and quoted multiline records; newline-ended passages
  do not claim an extra line.
- Only one unambiguous text/content/body field is selected automatically. Other or
  ambiguous schemas require `--text-field`. Metadata stays separate from searchable
  bodies; question/evaluation records and tool artifacts are rejected as documents.
- Include/exclude patterns and file/byte/record/extracted-character budgets are
  configurable. Skipped files, failed extractions and parser warnings are distinct
  in terminal and exports. Global budgets fail rather than silently drop inputs.
- CLI overrides environment, explicit config, user config and defaults, in that
  order. Explicit dotenv values sit below process environment. Config-relative
  paths, missing/invalid settings, list environment values and platform config paths
  have tests. No cwd config/dotenv discovery occurs. Provider secrets are excluded
  from all artifacts, including explicit-env-file runs.
- Old `portable-text-v1` preparation serialization retains its original shape for
  identity validation. New runs identify `portable-files-v1` and record ingestion policy.
- Reviewed fixtures independently specify visible HTML, JSON records, multiline CSV,
  JSONL physical lines and a manually authored three-page PDF with an image-only
  middle page. Real parser tests cover empty, encrypted, malformed and limited PDFs.

## Shared architecture changes

- Canonical JSON preserves meaningful list order and sorts sets before serialization.
  New runs identify schema/hash versions and corpus, questions, references,
  representation, configuration and exact context independently.
- One run validator verifies the dataset binding, question completeness/uniqueness,
  ranks, sources, evidence and exact context before scoring or generating answers.
- Retrieval stages receive source text/IDs without gold evidence labels. Labels are
  reattached from authoritative sources after retrieval; expected answers are not
  exposed to query/retrieval stages.
- Modern evaluation artifacts retain private snapshot/run provenance. Comparison
  and report creation verify their metrics against that provenance. Exported reports
  omit the internal validation snapshot. Legacy evaluations remain explicitly labeled.
- Native/portable execution share configuration resolution, pipeline construction,
  ranking execution, context assembly, artifact storage and report-format dispatch.
- Embedding/cache boundaries reject malformed, nonfinite, zero or nonnumeric vectors;
  provider/endpoint/encoding identity prevents reuse across incompatible providers.
  Imported hit tails are validated before truncation, and missing timing is null.
- Existing tutorial, benchmark, import, evaluate, compare, generate and report
  workflows remain on the shared contracts. The tutorial and release fixtures pass.

## Verification

```bash
uv sync --frozen --dev --extra pdf
.venv/bin/ruff check src tests scripts
.venv/bin/pytest
.venv/bin/ragvi verify
uv build
.venv/bin/python scripts/check_portable_install.py
git diff --check
```

The test suite contains **196 passing tests** with the PDF extra installed (150 at
the M1/M2 commit boundary, plus 46 M3 checks). It includes
cross-process hash-seed checks for dataset identities and saved evaluations;
tampered artifacts; missing/duplicate questions; forged evidence/context; invalid
provider vectors/indexes/caches; input extraction/offsets; question-file exclusion;
explicit failed-run artifacts; source-only behavior; prompt/flag modes; all output
formats; escaped source content; and unchanged source files.

The built wheel was installed into isolated temporary tool/bin directories and
invoked as `ragvi` from an unrelated customer folder. Checks cover spaces and Unicode
in paths, all three exports, source-only execution, HTML/JSON/JSONL/CSV loading,
explicit configuration, missing optional PDF support, installation verification and
the existing tutorial. CI and release preparation run this same check, and install
the PDF extra for the real parser tests. These runs
was on Linux; it is not evidence of Windows/macOS execution.

## Remaining roadmap work

- Direct portable entry points and reviewed span-based scoring for other techniques,
  with a capability catalog and complete stage traces.
- Multi-technique comparison/suite commands, split/slice aggregation, fair token
  budgets, uncertainty/resource summaries and decision reports.
- Metadata filters, MMR, automatic rewriting and extractive compression.
- Optional answer/citation/abstention evaluation and calibrated model judges.
- Pinned model-revision fingerprints where provider APIs expose them, plus the
  wider model/OS coverage and release gates specified by later milestones.

These remaining features are not claimed by the portable BM25 implementation. PDF/
HTML extraction does not establish visual/table/column fidelity; input limits are
not a memory sandbox. Windows/macOS installed execution remains unverified.
