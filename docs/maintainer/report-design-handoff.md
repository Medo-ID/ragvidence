> The report grid and optional theme-toggle revision supersedes this visual
> direction. See [the current design review](report-grid-review.md). This file and
> its packet describe the prior revision and retain its original evidence.

# Dark HTML reports: website and video handoff

The report presentation is implemented for the **unpublished 0.2.1 candidate**.
Implementation commit: `e293807526d184932aa00e508df6b8388003dfd0`.
Review branch: `verification/dark-html-reports` against `main`.
The branch also contains CI diagnostics and an Ubuntu test-discovery correction.
Use `git rev-parse HEAD` and the review packet for the final branch identity.
All maintainer commits use **Medo-ID <midaghdour@gmail.com>**.

Production remains **0.2.0**. No tag was created or moved, no index upload was
performed, and nothing was merged or published. Publishing 0.2.1 requires separate
authorization and the existing TestPyPI → verified candidate → production flow in
[releasing.md](releasing.md). Preserve the original `dist/release/` artifacts and
`v0.2.0` tag (`fba0c92ddaeb414ba8e9f0dea0e0c93f4e9c29f4`). Their hashes remain:

- Wheel: `ef300e798bc7cad72a560dc2a6c6c9819737bdbac9241f7ebf2a593a5f2c54e9`
- Sdist: `654a3ea0b1429ea72618501f205a97efb33965ff94775fe2f628f1ded008be0b`

## Scope and review

Inspection, technique comparison and tutorial/workspace reports now share the
same soft charcoal surfaces, Geist typography, borders, focus styling, navigation,
responsive tables and print rules. Configuration, identifiers, intervals and raw
stage JSON use native disclosures. Evidence outcomes and partial failures remain
visible before detailed traces. Missing measurements retain N/A; the comparison
shows known/missing timing counts and supplied-cost provenance.

`html.py` and `render.py` were inspected and left unchanged. Only presentation,
packaging guards, review tooling, tests, release version metadata and handoff docs
changed. Retrieval, scoring, authoritative JSON and Markdown, schemas, source
spans and returned text are unchanged. Reviewed/unreviewed scope, imported proxy
limits, dev/heldout boundaries and reuse disclosures remain intact.

The website repository was kept read-only. No website redesign, sample replacement,
video recording, deployment, release tagging or publication occurred here.

## Reproduce the previews

Use Python 3.12 and the repository's frozen development environment with all extras.
The review scripts use existing Playwright and pypdf installations; neither is a
new report runtime dependency. Select an existing Playwright module explicitly.
Reports themselves contain no JavaScript or external assets.

```bash
uv sync --frozen --dev --all-extras
uv run --no-sync python -m scripts.generate_report_previews --root verification/ci/new-report-review --phase accepted
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node scripts/review_report_previews.mjs verification/ci/new-report-review accepted
```

The browser reviewer expects a `before/manifest.json` as well. To recreate a genuine
baseline with the same fixtures, first extract the original CLI source to a separate
temporary directory and run the maintained generator against that source:

```bash
mkdir -p /tmp/ragvidence-report-baseline
git archive adfa659b97ac39bbba20a3c3b0df57757462aa8d src | tar -x -C /tmp/ragvidence-report-baseline
PYTHONPATH=/tmp/ragvidence-report-baseline/src .venv/bin/python -m scripts.generate_report_previews --root verification/ci/new-report-review --phase before
```

Run the baseline command before generating `accepted`. Use a fresh output root;
the generator refuses to overwrite an existing phase. On Windows use the equivalent
PowerShell environment assignment and Python executable path. The existing local
packet was generated on Linux. No Windows manual review is claimed.

The generator writes deterministic synthetic source, question, reviewed-span,
imported-result and suite fixtures under `fixtures/`, and saves every actual CLI
invocation in `<phase>/commands.txt`. It invokes real CLI commands and never edits
generated report results. Run IDs, timestamps and measurements vary between runs.
Reviewed offsets and source IDs are derived from the real loader. The suite uses
bootstrap seed 42 and 100 samples, with an empty slice for N/A intervals. It includes
an exact-span imported baseline, lexical and parent-child retrieval; a separate
plain-text heading-context run intentionally fails. Source-only input includes an
empty file and unsupported input notices. Long paths, long passages, HTML-like
source text, French, Japanese and Arabic are synthetic.

## Local review packet

Paths below are relative to `verification/ci/report-design/` in the CLI checkout.
Generated files are ignored, local artifacts; a fresh clone must regenerate them.
`before/` contains the genuine original reports; `accepted/` is the final visual
candidate. `after/` and `final/` retain intermediate reviews and are not the handoff
samples. `accepted/manifest.json` contains the complete report SHA-256 values.
`packet.json` binds final source identity, reports, fixtures, screenshots, PDFs,
distributions and CI records. `index.html` opens all before/after previews and
captures. `pull-request.md` supplies the review description.

| Case | Generated HTML path | SHA-256 | Captures / PDF (same directory) |
| --- | --- | --- | --- |
| comparison | `accepted/comparison/comparison-manual-caf-long-path-long-path-long-path-long-pat-20261018T204952-695fe277d58a/exports/a45085445351418e91ce8930f7dd067f/report.html` | `09265b69d97f9a60637876b2b92e0faf32e69eafb7635c1e51a5715b4b23cda2` | `browser/accepted/comparison-overview-1440.png`, `comparison-overview-390.png`, `comparison-expanded-390.png`, `comparison.pdf` |
| failure | `accepted/failure/comparison-plain-20261018T204954-874686f1449a/exports/62f86b5329e144caaeaa1c5128957540/report.html` | `436726dd5283b4668cea64cc76a27e88ba82b71ef312ae882cf65c017be4608b` | `browser/accepted/failure-overview-1440.png`, `failure-overview-390.png`, `failure-expanded-390.png`, `failure.pdf` |
| retrieval | `accepted/retrieval/manual-caf-long-path-long-path-long-path-long-path-long-path-20261018T204950-3dc0f97c8536/report.html` | `a537fc6c110294c34b706bbbebd2e85acb2e51170f4b074bb23dd6b7954879b4` | `browser/accepted/retrieval-overview-1440.png`, `retrieval-overview-390.png`, `retrieval-expanded-390.png`, `retrieval.pdf` |
| reviewed | `accepted/reviewed/manual-caf-long-path-long-path-long-path-long-path-long-path-20261018T204951-98e7de8c0ba6/report.html` | `7f6852de01a4b36e0b255b4a4e3d84764480750769677b1e3d7f70e89710ff4e` | `browser/accepted/reviewed-overview-1440.png`, `reviewed-overview-390.png`, `reviewed-expanded-390.png`, `reviewed.pdf` |
| source-only | `accepted/source-only/fixtures-20261018T204949-2325b78cb1a7/report.html` | `0248a1d12a3d475a229aa31f0f06e14d4c5b2d3461b086fc33eee36754e9d19a` | `browser/accepted/source-only-overview-1440.png`, `source-only-overview-390.png`, `source-only-expanded-390.png`, `source-only.pdf` |
| tutorial | `accepted/tutorial/first-run/reports/tutorial.html` | `a5054e3ca7a309007c7bc7b0307c463e2d754c1b4531c239ab1e4770b404720b` | `browser/accepted/tutorial-overview-1440.png`, `tutorial-overview-390.png`, `tutorial-expanded-390.png`, `tutorial.pdf` |
| unscored | `accepted/unscored/comparison-manual-caf-long-path-long-path-long-path-long-pat-20261018T204953-d0afb43c2a52/exports/a5f7d0b8f6e6439496a399889a911f0c/report.html` | `57b54913de584058f6262c94ff7f42ee9c74ee81b9300d0c37ae44796ec5f551` | `browser/accepted/unscored-overview-1440.png`, `unscored-overview-390.png`, `unscored-expanded-390.png`, `unscored.pdf` |

Additional captures include full-page desktop/mobile, expanded desktop/mobile and
print-media screenshots. Each `browser/accepted/CASE.pdf` was generated while all
disclosures were closed. The paper styles print their contents without scripting
or manually opening them. `browser/checks.json` records browser assertions;
`evidence-checks.json` records unchanged evidence and PDF extraction results.

## Validation and practical limits

- Focused reporting/span/portable/comparison checks: 109 passed. Four real-command
  presentation regressions also verify escaping, embedded fonts, labels, navigation,
  source preservation and render purity. The failure case explicitly selects the
  comparison export rather than filesystem-dependent internal report discovery.
- Full shared gate: lint, all tests, four-target locked dependency preflight,
  capability contracts, `ragvi verify`, wheel/sdist inspection and three isolated
  installation modes. `committed-gate/` records the initial clean implementation
  (399 tests). The final gate record and exact head are linked from `packet.json`.
  The diagnostics regression adds one test to the final total.
- Packaging guards require all three templates, the shared CSS/macros, both Geist
  fonts and their license. Isolated wheel, source and optional-runtime installs
  generate inspection, comparison and tutorial reports outside the checkout.
- Browser review: 28 before/after views in Chromium, 1440×1000 and 390×1000,
  JavaScript disabled, offline, reduced motion; no remote requests, console errors,
  missing navigation targets or viewport overflow in final collapsed/expanded views.
  Keyboard disclosure activation, visible focus and mobile table scrolling pass.
  Visible sampled text meets 4.5:1 (3:1 for large text) computed contrast checks.
- Seven real PDFs contain every preformatted block from closed disclosures:
  passages, stage JSON, configuration, identifiers and font notices. Comparison
  PDFs can be long because complete evidence is deliberately printed. PDF extraction
  reorders Arabic glyphs, so the verifier checks every ASCII character of each full
  block; Unicode is preserved in HTML and inspected visually with local fallback fonts.
- Geist stays embedded. CJK rendering depends on installed fallback fonts. This host
  needed local Noto CJK fonts for review; those host-only files are not shipped.
  Chromium printing was validated; older engines may require opening disclosures
  manually if they lack `::details-content` print support. Other browser engines
  and human Windows usability were not manually reviewed. The deferred Windows
  review is not a blocker. This is a synthetic diagnostic example, not a benchmark.
- Hosted CI runs all five required checks (workflow lint and Linux, Windows, macOS
  ARM64/Intel). The initial Ubuntu-only failure was in the new test's export
  discovery, not the renderer. Retained public diagnostics and final observed
  outcomes are in `packet.json` and the branch's Actions history. Require all
  checks on the final head before merging; PR checks run again when it is opened.

## Website samples and next video

1. Open a separate website session, read its AGENTS.md and maintenance docs, and
   preserve its existing work. This CLI session has not changed that repository.
2. For a production sample, wait for separately authorized 0.2.1 publication, then
   use the exact published wheel in an isolated environment. Until then, these
   previews must be labeled an unpublished candidate; production 0.2.0 still has
   its original report styling. Do not imply 0.2.1 is available from PyPI.
3. Install the exact wheel without replacing the user's global CLI. Record its
   SHA-256, source/release commit, `ragvi --version` and `ragvi verify`. Use the same
   synthetic fixture generator with that environment's Python/CLI. Keep the fixture
   manifest and actual commands, settings, output hashes and question-level facts.
   Copy the complete generated HTML byte for byte to the website sample destination
   only in the website session; preserve notices and run the website's complete gate.
4. Lead the next recording with own data → questions → reviewed evidence → comparison.
   Show source-only and unscored scope, the exact-span imported baseline's N/A timing,
   a regression, an improvement, remaining failures and context-size trade-offs.
   The tutorial's 60% → 90% example is fictional and includes one unresolved failure;
   it does not establish answer/citation correctness or a general best technique.
5. Inspect the website's `scripts/record-walkthrough.mjs` before adapting it. Use
   `accepted/commands.txt` as the tested command source and the real generated HTML
   for browser shots. Open question disclosures with keyboard or clicks during
   recording. Never edit scores, context, run facts or failure labels for the video.
   Record CLI/wheel/report/website hashes and exact commands in media provenance.
   Include desktop/mobile report shots, captions and a poster. Resolve reduced-motion
   behavior and verify playback, encodings and accessibility in the website task.
6. Use a shorter synthetic filename for public media if desired, regenerate through
   the CLI and record the new hashes. Keep the long-path packet for robustness review.
   Website deployment and CLI publishing each require separate authorization.

## Owner actions

The branch is pushed and reviewable. Git SSH access is available; this environment
has no authenticated GitHub API client for opening a PR or merging protected main.
Open the prepared PR from `verification/dark-html-reports` to `main`, use the local
`pull-request.md`, review the previews, and require passing final-head checks. The
maintainer decides whether to merge and separately authorize a 0.2.1 release.
Do not create/push a release tag just to finish this presentation task.
