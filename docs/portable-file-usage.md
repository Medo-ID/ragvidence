# Portable file usage

Available in the development source and wheels built from it; not yet published
to PyPI. The first portable technique command is BM25 over TXT/Markdown files and
folders. Other raw-file techniques and input formats remain planned.

## Run on your own text

After installing the development wheel as a tool:

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
`question_id` and `question`. Use the existing workspace `evaluate` workflow for
reviewed evidence labels; raw-file reviewed scoring will arrive separately.

In a terminal, a command without questions offers question entry. Leave it empty
to inspect sources only. `--no-input` disables all prompts; redirected input also
never blocks. `--interactive` offers output format selection and requires terminal
input. Complete flags work without prompts.

- `ingestion_only`: loaded/split sources; retrieval was not executed.
- `retrieval_inspection`: retrieved actual passages for the supplied questions;
  relevance, evidence sufficiency and answer correctness have not been scored.

Both are successful execution states. Invalid inputs, unavailable output paths or
execution failures return a nonzero exit status. Low or zero BM25 scores are
observations, not command failures or probabilities of correctness.

## Files, passages and limits

UTF-8 `.txt`, `.md` and `.markdown` are supported. Markdown uses ATX headings
outside fenced code; heading paths and original character/line offsets are retained.
Setext headings and language-specific parsing are not supported. Source files are
never modified. UTF-8 decoding and Unicode lexical tokenization do not imply
language-specific stemming or semantic model support.

Folder discovery is recursive and deterministic. It skips hidden files/folders,
symbolic links, known generated directories, the selected question file and output
root, and directories marked as earlier RAGvidence runs. Skipped/invalid files are
listed in reports. An explicitly supplied invalid file fails with an explanation.

Current input limits: 1,000 supported files, 20 MiB per file and 100 MiB total loaded
file bytes. Large datasets need deliberate evaluation of memory and indexing time.

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
Share the selected report files rather than the entire working directory when the
original corpus should remain private. Reports can be read after cache deletion.

BM25 requires no model, API key or network requests. The portable path ignores any
`.env` in the data directory. `--cache-dir` overrides the platform user cache
location; BM25 does not create embedding/model caches.
