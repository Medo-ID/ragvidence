# Initial portable implementation evidence

Date: 2026-10-15. Scope: initial M1 integrity foundation and M2 portable BM25
workflow in the development source. No package has been published by this work.

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
.venv/bin/ruff check src tests scripts
.venv/bin/pytest
.venv/bin/ragvi verify
uv build
.venv/bin/python scripts/check_portable_install.py
git diff --check
```

The test suite contains **150 passing tests** at this delivery boundary. It includes
cross-process hash-seed checks for dataset identities and saved evaluations;
tampered artifacts; missing/duplicate questions; forged evidence/context; invalid
provider vectors/indexes/caches; input extraction/offsets; question-file exclusion;
explicit failed-run artifacts; source-only behavior; prompt/flag modes; all output
formats; escaped source content; and unchanged source files.

The built wheel was installed into isolated temporary tool/bin directories and
invoked as `ragvi` from an unrelated customer folder. Checks cover spaces and Unicode
in paths, all three exports, source-only execution, installation verification and
the existing tutorial. CI and release preparation run this same check. This run
was on Linux; it is not evidence of Windows/macOS execution.

## Remaining roadmap work

- Additional raw-file loaders: HTML, structured JSON/JSONL, CSV and optional PDFs.
- Direct portable entry points and reviewed span-based scoring for other techniques,
  with a capability catalog and complete stage traces.
- User-level configuration, explicit config/env-file options and further loader controls.
- Multi-technique comparison/suite commands, split/slice aggregation, fair token
  budgets, uncertainty/resource summaries and decision reports.
- Metadata filters, MMR, automatic rewriting and extractive compression.
- Optional answer/citation/abstention evaluation and calibrated model judges.
- Pinned model-revision fingerprints where provider APIs expose them, plus the
  wider model/OS coverage and release gates specified by later milestones.

These remaining features are not claimed by the portable BM25 implementation.
