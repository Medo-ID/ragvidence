# Report identity refinement

## Milestone 8 preparation — Compatible dependencies

Updated the lock within existing compatible ranges and installed the semantic
extra to inspect its metadata. The runtime license inventory now matches locked
versions. Ruff, 45 tests, ragvi verify, and wheel/sdist build pass. A fresh tutorial
matches the previous baseline exactly for every question metric, retrieved ID,
rank, score, and preview, as well as both summaries (6/10 and 9/10).

No retrieval code, metric definitions, or artifact schemas changed.
Report-template redesign is the next separate commit.

## Milestone 8 — Report source

Replaced the report presentation at the Jinja source: executive outcome,
baseline/intervention comparison, review-priority change groups, observed facts
versus diagnosis, and collapsed paired evidence investigation. All recorded metrics
and payload schema stay unchanged. Geist fonts and their OFL license are embedded.
Jinja escaping and StrictUndefined remain enabled; no scripts or remote assets.
Print exposes all closed question evidence and uses a white theme.

Ruff, 53 tests, installation verification, wheel/sdist build, and an installed-wheel
tutorial passed. Reports were reviewed through file:// with JavaScript disabled at
360/390/768/1280/1440/1920px with no overflow or remote requests. The website sample
must always be copied from generated output. Normal website Turbopack confirmation
is still reserved for the user's machine/Vercel.
