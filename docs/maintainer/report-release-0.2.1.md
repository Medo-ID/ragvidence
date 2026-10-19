# 0.2.1 HTML report release and website handoff

The owner approved the final report design and authorized pushing and releasing
**0.2.1** on 2026-10-19. The package, runtime and lockfile versions agree.
At preparation time, both PyPI and TestPyPI still publish 0.2.0; 0.2.1 is available
and remains unpublished until the publishing workflow succeeds. Preserve 0.2.0's
tag and original distributions.

## Review and publication

Review branch: `verification/dark-html-reports`, targeting `main`.
Use the [prepared comparison](https://github.com/Medo-ID/ragvidence/compare/main...verification/dark-html-reports)
and require passing hosted checks on the pushed head. Commit as
Medo-ID <midaghdour@gmail.com>. The local release packet is
`verification/ci/report-release-021/`; it records the exact pushed commit, CI run,
clean local gate, candidate artifact hashes and prepared PR/release notes.

Follow [the release procedure](releasing.md): merge the reviewed PR, dispatch
**Publish release** on **main** with **target: testpypi**, and require its platform
matrix and exact published-wheel installation to pass. Then tag that exact tested
commit `v0.2.1` and push the tag. Require PyPI publication, the production installed
wheel check and GitHub Release creation to succeed, and compare both indexes'
artifact hashes. Do not change package contents between candidate and production.

This session has Git SSH access but no authenticated GitHub API/CLI session.
Opening/merging the PR and dispatching TestPyPI require an authenticated owner.
The owner has already authorized subsequent production publication; another
general release confirmation is unnecessary once the prerequisites pass.
Do not bypass the PR/TestPyPI flow by pushing a production tag early.

## Shipped design and boundaries

All three report types share the [approved design contract](report-grid-review.md):
1100px centered single-column frame, aligned thin rails, full-width dividers,
Woodsmoke dark default, optional local light/dark toggle, embedded Geist fonts,
16px toolbar padding and a single horizontally scrollable navigation row at
800px and below. Native focus and arrow-key navigation work without JavaScript.
Configuration, hashes and stage JSON use native disclosures; paper styles include
their complete evidence even when closed.

Retrieval, scoring, source spans, exact returned context, authoritative JSON and
Markdown, schemas, failures, N/A values and evaluation boundaries are unchanged.
There are no new report runtime dependencies or remote assets. Generated answers
and citations are not judged, and comparisons do not select an automatic winner.

Local environments, editor/agent settings, credentials, caches, test outputs,
browser captures, new verification output and `report_UI.png` are ignored.
Existing tracked canonical evidence, maintained tests, fixtures, checks and shared
configuration remain retained. Distribution guards reject local development
material and provider dotenv files while allowing `.env.example` and shared tests.

## Previews and verification

The approved packet is `verification/ci/report-mobile-nav/index.html`;
`accessible/manifest.json` has real HTML paths and SHA-256 values for all seven
synthetic journeys. `packet.json` links fixtures, commands, screenshots, 14 PDFs,
browser checks and the pre-release development gate. Outputs are local and ignored;
fresh clones regenerate them rather than relying on committed reports.

The approved visual review passed 70 offline Chromium checks at 320, 390, 768,
900, 1440 and 1920px, including both themes, JavaScript disabled, keyboard access,
contrast, overflow, closed-disclosure printing and zero remote requests/errors.
Every PDF preformatted block was extracted and checked. The release packet records
the subsequent complete gate after the ignore/package-guard changes.

Limits: manual visual review covers Linux Chromium. Other engines and a human
Windows review remain unverified; the deferred Windows review is not a blocker.
Scripts outside Geist depend on host fallback fonts. Older print engines may
require opening disclosures manually. Synthetic results are not a benchmark.

## Next website and video session

Keep `../ragvidence-web` read-only during this CLI task. In the separate session,
read its instructions and inspect its status/diff before editing. Preserve its
existing work. Use this design's colors, typography, rectangular frame and control
states; adapt navigation and content hierarchy to the website's actual users.

After verified publication, download the exact **production 0.2.1 wheel**, check
its release SHA-256 and install it in a fresh environment. Record CLI tag/commit,
wheel hash, website commit and browser/tool versions. Use a fresh output root and
the maintained fixture generator; `PYTHONPATH` can point to that isolated install's
site-packages so the generator's subprocesses use the published package:

```bash
PYTHONPATH=/absolute/isolated/site-packages /absolute/isolated/bin/python -m scripts.generate_report_previews --root verification/ci/website-021 --phase published
```

Run this command from the CLI repository so the maintained script is available;
do not use an editable checkout as the CLI implementation. The fixture generator
records every real command in `published/commands.txt`. Its bundled tutorial uses
`ragvi tutorial --root DIRECTORY`; use the exact recorded command and copy only
reviewed synthetic HTML to the website sample location.
Preserve N/A values, regressions, failures, notices, provenance and limitations.

Before recording, pass the website's own required checks, responsive/accessibility
review and reduced-motion checks. Record genuine terminal commands, open the
generated report in both themes, demonstrate mobile navigation, expand question
evidence and show the print view. Use the existing website recording scripts after
reviewing their instructions. Retain command transcripts, sample/video hashes and
release identities. Website deployment needs its own authorization.
