# Pre-merge status — 2026-10-05

All implementation outside the owner-reserved HTML template is complete. The
owner's metrics contribution has been reviewed, cleaned, integrated, and accepted.

## Verified

- Dependency lock resolves without changes.
- Ruff passes across `src` and `tests`.
- All 38 tests pass.
- Wheel and source distribution build successfully.
- A clean wheel installation completes health, quickstart, validation and the BM25 benchmark.
- `raglab verify` passes asset hashes, dataset integrity, tokenizer, BM25, recovery, and metrics fixtures.
- Only the HTML template fixture remains blocked.

## Owner integration points

1. Add `src/raglab/reporting/templates/report.html.j2` using `docs/html-template-contract.md`.
2. Run the complete suite and `raglab verify`; no fixture may remain failed or blocked.
3. Generate measured BM25 and semantic reports from the shipped exercise before using improvement claims.

No release should be sold until the owner chooses a product license/EULA and completes the commercial items in `docs/release-checklist.md`.
