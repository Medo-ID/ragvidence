# Portable file usage

These portable workflows are included from version 0.2.0; use a matching release
or source build. Version 0.1.0 lacks them. Portable BM25, semantic, hybrid, reranking,
parent-child, heading/contextual
indexing, supplied multi-query and existing-system imports share TXT, Markdown,
HTML, document JSON/JSONL, CSV and optional text-bearing PDF loaders. See
[techniques and reviewed evidence](portable-techniques.md) for commands and scoring.
Use [portable comparisons](portable-comparisons.md) to run selected alternatives
against the same frozen inputs and export one decision report.

## Run on your own text

After installing a matching wheel as a tool:

```bash
ragvi bm25 ./manual.txt --query "How do I reset the device?"
ragvi bm25 ./docs --questions ./questions.txt --no-input
ragvi bm25 ./manual.md --query "Reset procedure" --format html --format json --format markdown
```

From the source checkout, prefix these commands with `uv run`. There is no `init`
step or manual workspace preparation for these commands.

The terminal shows source/passage counts, returned text and report paths. HTML is
the default export. Repeat `--format` to choose exports; an explicit selection
replaces the default. Reports use a new directory below `./ragvi-reports/` on each
run. `--output DIRECTORY` chooses another root. `--open` opens the saved HTML when
a browser is available; no browser opens by default.

## Questions and status

Use repeatable `--query` flags or `--questions FILE`. TXT question files use one
question per nonblank line. JSON may be an array of question strings or objects;
JSONL uses one object per line:

```json
{"question_id":"Q-1","question":"How do I reset the device?"}
```

Question IDs must be unique. Portable question records currently accept only
`question_id` and `question`. Supply `--reviewed FILE` instead for reviewed questions
and evidence anchored to original text spans; see the linked technique guide.

In a terminal, a command without questions offers question entry. Leave it empty
to inspect sources only. `--no-input` disables all prompts; redirected input also
never blocks. `--interactive` offers output format selection and requires terminal
input. Complete flags work without prompts.

- `ingestion_only`: loaded/split sources; retrieval was not executed.
- `retrieval_inspection`: retrieved actual passages for the supplied questions;
  relevance, evidence sufficiency and answer correctness have not been scored.

`reviewed_evaluation` is the scored state when validated reviewed references are
supplied. All three are successful execution states. Invalid inputs, unavailable output paths or
execution failures return a nonzero exit status. Low or zero BM25 scores are
observations, not command failures or probabilities of correctness.

## Files, passages and limits

UTF-8 `.txt`, `.md` and `.markdown` are supported. Markdown uses ATX headings
outside fenced code; heading paths and original character/line offsets are retained.
Setext headings and language-specific parsing are not supported. Source files are
never modified. UTF-8 decoding and Unicode lexical tokenization do not imply
language-specific stemming or semantic model support.

Additional formats:

| Input | Searchable content and retained location |
| --- | --- |
| `.html`, `.htm` | Visible text grouped by headings; section number and heading path. Scripts, styles, head, template, noscript and hidden/aria-hidden elements are excluded. No remote assets or scripts run. CSS layout and dynamic content are not interpreted. |
| `.json` | One document object or an array of objects; one text field per record and record number. |
| `.jsonl` | One document object per nonblank line; record number and original file line. |
| `.csv` | Header plus document rows; one text column, data-row number and physical line range, including quoted multiline cells. Comma delimiter, unique headers and consistent row widths required. |
| `.pdf` | Text-bearing pages with original page numbers and parser version. Install `ragvidence[pdf]` with your tool installer; nothing downloads automatically. Encrypted PDFs fail; textless pages are reported; fully scanned/empty PDFs fail with an OCR explanation. |

JSON/JSONL/CSV select a single unambiguous `text`, `content` or `body` field. If
multiple fields exist or another name is used, supply `--text-field NAME`. Every
record must contain nonempty string text in that field. Nested values remain
metadata; they are never flattened into the searchable text. Question/evaluation
records (including reference answers) and RAGvidence artifacts are rejected as
document inputs. Use document-only exports for these loaders.

```bash
ragvi bm25 ./articles.json --text-field article --query "Reset procedure"
ragvi bm25 ./data --include '*.jsonl' --include '*.csv' --exclude 'drafts/*' --no-input
```

PDF/HTML text extraction does not validate visual fidelity, table relationships,
columns or OCR quality. PDF parsing uses [pypdf's text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html),
which does not perform OCR. The report shows extraction warnings. Character and
text-line offsets refer to the extracted record/page/section, not original file
bytes; original page/row/record locations are retained separately.

Folder discovery is recursive and deterministic. It skips hidden files/folders,
symbolic links, known generated directories, the selected question file and output
root, and directories marked as earlier RAGvidence runs. Skipped/invalid files are
listed in reports. An explicitly supplied invalid file fails with an explanation.

Default limits: 1,000 supported files, 20 MiB per file, 100 MiB total attempted file
bytes, 10,000 records/HTML sections/PDF pages per file and 20 Mi characters extracted
across the corpus. Override with `--max-files`, `--max-file-bytes`, `--max-total-bytes`,
`--max-records` and `--max-extracted-characters`. Total budgets fail the command;
per-file extraction errors in folders are listed while valid files proceed. If no
usable text remains, the command fails. These are input/output limits, not a parser
memory sandbox; decompression/parsing and indexing can require additional memory.

`--include` and `--exclude` are repeatable, case-sensitive glob patterns against
relative POSIX file paths; exclusions win. `*` also matches slashes. Directory
exclusions built into discovery still apply. Notices distinguish intentionally
skipped files, failed extraction and parser warnings in the terminal and reports.

Default passages are at most 500 body characters with 50 characters of overlap.
Use `--chunk-size` and `--chunk-overlap`; overlap must be smaller than size.
Markdown overlap stays within sections. These are character counts, not tokens.
`--k` controls how many passages are returned, up to the available count.

## Reports and internal artifacts

The HTML report contains no scripts or remote assets and can be opened locally or
shared. HTML, JSON and Markdown exports contain retrieved passages and their source
locations. Review those contents before sharing.

The run directory also contains private working artifacts: `snapshot.json` has
the loaded source text; `questions.json` records input questions; `run.json` records
exact returned context and configuration; `status.json` records completion/failure.
`search-sources.json` freezes search bodies/prefixes; reviewed runs also retain
`references.json` and `evaluation.json` with span-based scoring.
Share the selected report files rather than the entire working directory when the
original corpus should remain private. Reports can be read after cache deletion.

BM25 requires no model, API key or network requests. The portable path ignores any
`.env` in the data directory unless explicitly selected. `--cache-dir` overrides the platform user cache
location; BM25 does not create embedding/model caches.

## Portable configuration

Values resolve in this order: **CLI flags → environment → explicit `--config` →
user configuration → defaults**. An explicitly selected `--env-file` contributes
environment values below actual process environment variables. Neither a current
directory config nor a dotenv file is discovered automatically.

`--config FILE` accepts TOML or JSON with flat portable option names. Unknown keys
fail. Relative `output`/`cache_dir` paths in configuration files resolve relative
to that file; flag/environment paths resolve from the invocation directory.

```toml
k = 3
formats = ["html", "json"]
chunk_size = 500
chunk_overlap = 50
output = "reports"
include_patterns = ["*.md", "*.jsonl"]
```

All portable options have an environment equivalent: `RAGVIDENCE_K`,
`RAGVIDENCE_OUTPUT`, `RAGVIDENCE_CACHE_DIR`, `RAGVIDENCE_TEXT_FIELD`, etc. Lists use
JSON arrays, for example `RAGVIDENCE_FORMATS='["html","json"]'`. Queries/questions,
interactive behavior, browser opening and credential settings are not portable
config keys. Provider settings keep their existing `RAGVIDENCE_EMBEDDING_*` /
`RAGVIDENCE_GENERATION_*` names; credentials are not serialized into reports.

User configuration location:

- Linux: `$XDG_CONFIG_HOME/ragvidence/config.toml`, default `~/.config/ragvidence/config.toml`.
- macOS: `~/Library/Application Support/ragvidence/config.toml`.
- Windows: `%APPDATA%/ragvidence/config.toml`, default `~/AppData/Roaming/ragvidence/config.toml`.

Use `--output` and `--cache-dir` to select writable destinations when inputs are
read-only. Selected question/config/env files, output and cache roots are excluded
from folder ingestion. Settings resolution and path selection have automated
platform tests; installed-command execution has currently been verified on Linux.
