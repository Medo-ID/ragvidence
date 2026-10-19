# Centered single-column CLI report: design review

The owner-provided `report_UI.png` now defines the frame geometry. This local
revision supersedes the previous boxed-document and background-grid proposals.
The owner approved this design and authorized pushing and releasing 0.2.1.
Keep `../ragvidence-web` read-only in this CLI session. Website changes and
deployment belong to the next session.
Version 0.2.1 is still an unpublished candidate. Do not replace 0.2.0 artifacts or
move its tag. The prior packets and verification evidence remain unchanged. See
[the 0.2.1 release handoff](report-release-0.2.1.md) for current publication status.

## Design contract for reports and the later website session

The report has exactly one centered content column, capped at 1100px. The side
cells and the top band stay empty. Two vertical rails continue through that empty
space; thin horizontal section boundaries span the full page width. The page and
report share one background. Each section has generous 48px internal padding,
reduced to 32px on narrow screens. Corners are square and there are no shadows.
Outer whitespace is 160px above/below on desktop and 64px on narrow screens;
side gutters are at least 48px on desktop and 24px on narrow screens.
The toolbar has 16px vertical padding, matching navigation. Run summaries have no top border or extra
padding, and question lists have no top border. Box sizing is scoped to the main
frame and its continuing rails so both strokes coincide; there is no universal
box-sizing rule.

Use Tailwind's `bg-gray-100` background in light mode.
Woodsmoke is a custom palette: the owner supplied **1000 = #010101** and
**900 = #16161b** as the dark palette. These exact owner tokens remain embedded.
The subsequent refinement increases divider contrast slightly: `#28282e` in dark
mode and `#c6cbd3` in light mode (slightly stronger than gray-300).
Tailwind's gray values are
embedded as [official theme tokens](https://github.com/tailwindlabs/tailwindcss/blob/main/packages/tailwindcss/theme.css);
there is no Tailwind dependency or remote runtime stylesheet.

Native disclosures, jump navigation, semantic badges and embedded Geist fonts
remain. Labels distinguish execution completion from scored evidence sufficiency.
Source passages, spans, hashes, failures, N/A values and all authoritative report
facts are preserved. This visual update does not modify retrieval or scoring.

The source of truth for styling is
`src/ragvidence/reporting/templates/_styles.css.j2`. Shared native controls live
in `_toolbar.html.j2` and `_labels.html.j2`; `_theme.js.j2` contains the only report
script. All are embedded into each generated file and included in the wheel.

| Token | Dark default | Light |
| --- | --- | --- |
| Canvas | `#010101` | `gray-100`: `oklch(96.7% 0.003 264.542)` |
| Document | Same as canvas | Same as canvas |
| Raised surface | `#1b1b1b` | `#ffffff` |
| Text | `#eceef2` | `#202126` |
| Secondary text | `#a7abb5` | `#5d626d` |
| Divider | `#28282e` | `#c6cbd3` |
| Pass / improvement | `#7bdba5` | `#176c40` |
| Failure / regression | `#ff9ba5` | `#b32b40` |
| Warning / unresolved | `#f0cb7b` | `#805710` |
| Information / completed execution | `#96bcff` | `#275bad` |

Unscored and unavailable values stay neutral with explicit N/A labels. Completion
of execution is blue, separate from green evidence sufficiency. All component
corners are square. CSS Grid uses exactly one content column at every breakpoint,
including comparisons and outcomes. Geist Mono identifies metadata and numeric
summaries; source passages use Geist. Wide tables remain inside labeled,
keyboard-scrollable regions. Decorative full-width lines are clipped at the
viewport edge and never create a horizontal page scrollbar.
Navigation fits on one line at desktop sizes and wraps at intermediate widths.
At 800px and below, links stay on one row and the navigation scrolls horizontally
without widening the page. Native arrow-key scrolling and Tab access to every
link work without JavaScript. The named navigation region is keyboard-focusable,
with the same visible focus treatment as other controls. Navigation stays in document flow below 1200px so
anchor targets remain visible; desktop navigation remains sticky.

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

The new local packet is `verification/ci/report-mobile-nav/`. `before/` contains reports
from the preceding implementation; `accessible/` contains real CLI outputs with this
revision. Each phase contains actual generation commands and HTML SHA-256 values.
The inputs, original spans, scores, exact returned contexts and question-level
changes are checked against the earlier generation. Timings and run IDs vary.

```bash
mkdir -p /tmp/ragvidence-grid-baseline
git archive 53b87c2d2174783eb4c450e947853369bff56565 src | tar -x -C /tmp/ragvidence-grid-baseline
PYTHONPATH=/tmp/ragvidence-grid-baseline/src .venv/bin/python -m scripts.generate_report_previews --root verification/ci/fresh-grid-review --phase before
uv run --no-sync python -m scripts.generate_report_previews --root verification/ci/fresh-grid-review --phase accessible
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node scripts/review_report_previews.mjs verification/ci/fresh-grid-review accessible
uv run --no-sync python -m scripts.verify_report_previews --root verification/ci/fresh-grid-review --after accessible
```

Use fresh phase names; do not overwrite reports or hand-edit generated facts.
The packet index links actual dark/light desktop/mobile screenshots, all seven
report cases, print PDFs, fixtures and commands. `browser/checks.json` records
JavaScript-disabled and enabled theme checks, plus actual layout measurements
at 320, 390, 768, 900, 1440 and 1920px. These assert a centered 1100px maximum, one
column, 32–48px section padding, empty surrounding cells, 1px full-width boundaries,
continuous vertical rails with matching outer edges, compact toolbar padding,
matching page/document backgrounds and single-row mobile navigation with keyboard
scrolling and Tab access to the final link. Desktop navigation fits without
horizontal scrolling. `evidence-checks.json` records
unchanged evidence and PDF extraction. The final local gate is `gate-accessible/checks.json`;
CI identity and outcomes belong to the packet's provenance record. The old
packet's CI results are evidence for its older revision only.

## Website handoff after verified publication

In the separate website session, re-read its AGENTS.md and maintenance guidance,
inspect its status/diff, and preserve existing work. Use these colors, typography,
component states and centered single-column document layout as the approved design contract. Adapt the
website's actual navigation and content to its users; report density and evidence
hierarchy stay specific to the CLI. Record CLI and website commits in the sync
handoff and update screenshots/tests together.

Generate public samples and the next video from the exact verified 0.2.1
published wheel. Until then, label these previews an unpublished 0.2.1 candidate.
Use genuine CLI commands, retained failures and N/A values; preserve notices and
hashes. The existing report-design handoff covers the sample/video provenance and
release procedure. Do not start website edits or recording as part of this design
review. Release authorization has been provided; website deployment still
requires authorization in its own session.
