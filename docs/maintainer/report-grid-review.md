# CLI report grid: design review

This revision supersedes the visual direction in the previous dark-report packet.
The design is **awaiting owner visual confirmation**. Keep `../ragvidence-web`
read-only until that confirmation; publishing and deployment remain separate.
Version 0.2.1 is still an unpublished candidate. Do not replace 0.2.0 artifacts or
move its tag. The prior packet and verification evidence remain unchanged.

## Design contract for reports and the later website session

The report is a compact CLI document: a single bordered frame, continuous thin
section dividers, a subtle square grid in the surrounding canvas, small monospace
metadata, ordinary readable source text, restrained badges and native disclosures.
There are no marketing sections, large hero numbers or decorative panels. Jump
navigation stays available while scrolling. Use actual report labels and facts;
color is supplementary information.

The references were inspected visually: [AdonisJS](https://adonisjs.com/) for its
aligned page frame and separators; shadcn's [badges](https://ui.shadcn.com/docs/components/badge)
and [buttons](https://ui.shadcn.com/docs/components/button) for their restrained
scale, borders and states. The implementation is plain CSS and native HTML; it
adds no shadcn, Tailwind, framework or chart dependency.

The source of truth for styling is
`src/ragvidence/reporting/templates/_styles.css.j2`. Shared native controls live
in `_toolbar.html.j2` and `_labels.html.j2`; `_theme.js.j2` contains the only report
script. All are embedded into each generated file and included in the wheel.

| Token | Dark default | Light |
| --- | --- | --- |
| Canvas | `#111214` | `#f3f4f6` |
| Document | `#17181b` | `#ffffff` |
| Raised surface | `#202125` | `#f6f7f9` |
| Text | `#eceef2` | `#202126` |
| Secondary text | `#a7abb5` | `#5d626d` |
| Divider | `#36383e` | `#d5d8df` |
| Pass / improvement | `#7bdba5` | `#176c40` |
| Failure / regression | `#ff9ba5` | `#b32b40` |
| Warning / unresolved | `#f0cb7b` | `#805710` |
| Information / completed execution | `#96bcff` | `#275bad` |

Unscored and unavailable values stay neutral with explicit N/A labels. Completion
of execution is blue, separate from green evidence sufficiency. Card/control
corners are 4–5px; the outer frame and section grid are square. The grid step is
48px. Geist remains embedded for text; Geist Mono is used for identifiers and
numeric summaries. Heading sizes are 26/18/15px, body 14px and metadata 11–12px.
Report content stays fluid, wraps long paths, and keeps wide tables inside labeled,
keyboard-scrollable regions. Narrow screens keep 16px exterior margins.

## Theme behavior and safety

Dark is the default even when the host prefers light. The optional native button
switches this document between dark and light and updates its accessible pressed
state and action label. Theme selection is intentionally local to the open report:
there is no storage, network request, telemetry, dependency or content processing.
The script never interpolates source/report data. It has no effect on retrieval,
scoring, evidence, disclosures, navigation or print output. JavaScript-disabled
reports remain fully readable in dark mode and hide the inactive theme button.
Printing always uses paper colors and includes closed disclosures in supported
browsers. The test guard permits exactly the trusted static theme script; hostile
source scripts remain escaped.

## Reproduce and inspect

The new local packet is `verification/ci/report-grid/`. `before/` contains reports
from the preceding implementation; `proposal/` contains real CLI outputs with this
revision. Each phase contains actual generation commands and HTML SHA-256 values.
The inputs, original spans, scores, exact returned contexts and question-level
changes are checked against the earlier generation. Timings and run IDs vary.

```bash
mkdir -p /tmp/ragvidence-grid-baseline
git archive 6769433cc79d67fc0cdae21b641a02a23ec439a9 src | tar -x -C /tmp/ragvidence-grid-baseline
PYTHONPATH=/tmp/ragvidence-grid-baseline/src .venv/bin/python -m scripts.generate_report_previews --root verification/ci/fresh-grid-review --phase before
uv run --no-sync python -m scripts.generate_report_previews --root verification/ci/fresh-grid-review --phase proposal
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node scripts/review_report_previews.mjs verification/ci/fresh-grid-review proposal
uv run --no-sync python -m scripts.verify_report_previews --root verification/ci/fresh-grid-review --after proposal
```

Use fresh phase names; do not overwrite reports or hand-edit generated facts.
The packet index links actual dark/light desktop/mobile screenshots, all seven
report cases, print PDFs, fixtures and commands. `browser/checks.json` records
JavaScript-disabled and enabled theme checks. `evidence-checks.json` records
unchanged evidence and PDF extraction. The final local gate is `gate/checks.json`;
CI identity and outcomes belong to the packet's provenance record. The old
packet's CI results are evidence for its older revision only.

## After the owner confirms this direction

In the separate website session, re-read its AGENTS.md and maintenance guidance,
inspect its status/diff, and preserve existing work. Use these colors, typography,
component states and grid alignment as the approved design contract. Adapt the
website's actual navigation and content to its users; report density and evidence
hierarchy stay specific to the CLI. Record CLI and website commits in the sync
handoff and update screenshots/tests together.

Generate public samples and the next video from the exact separately authorized
published wheel. Until then, label these previews an unpublished 0.2.1 candidate.
Use genuine CLI commands, retained failures and N/A values; preserve notices and
hashes. The existing report-design handoff covers the sample/video provenance and
release procedure. Do not start website edits or recording as part of this design
review, and do not treat visual approval as release/deployment authorization.
