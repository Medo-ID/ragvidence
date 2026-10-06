# Pre-merge status — 2026-10-05

All implementation outside the two owner-reserved contributions is complete.

## Verified

- Dependency lock resolves without changes.
- Ruff passes across `src` and `tests`.
- 25 non-reserved tests pass.
- Wheel and source distribution build successfully.
- A clean wheel installation completes health, quickstart, validation and the BM25 benchmark.
- `raglab verify` passes asset hashes, dataset integrity, tokenizer, BM25 and recovery fixtures.
- The complete suite has exactly 13 expected failures, all in the unimplemented owner metrics.

## Owner integration points

1. Replace `src/raglab/evaluation/metrics.py` with the owner implementation and run `tests/unit/test_metrics.py`.
2. Add `src/raglab/reporting/templates/report.html.j2` using `docs/html-template-contract.md`.
3. Run the complete suite and `raglab verify`; no fixture may remain failed or blocked.
4. Generate measured BM25 and semantic reports from the shipped exercise before using improvement claims.

No release should be sold until the owner chooses a product license/EULA and completes the commercial items in `docs/release-checklist.md`.
