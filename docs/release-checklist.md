# Release checklist

## Code and data

- [ ] Owner metrics contribution passes every metric contract test.
- [ ] Owner HTML template passes escaping, offline and layout tests.
- [ ] `uv run ruff check src tests` passes.
- [ ] Full `uv run pytest` passes.
- [ ] `uv run raglab verify` reports no failure or blocked fixture.
- [ ] Guided BM25 workflow runs from a clean extracted archive.
- [ ] Semantic workflow is tested after the pinned model download.
- [ ] Wheel and source archive contain exercise JSONL, integrity manifest and documentation.

## Product truthfulness

- [ ] Every advertised command exists in the release.
- [ ] No paid/advanced feature is described as already included.
- [ ] Measured results are generated from the shipped release.
- [ ] Limitations, dataset size and tested environments are visible.
- [ ] Product screenshots/reports contain no secrets or private customer data.

## Licensing and commerce

- [ ] Owner chooses the product’s license/EULA before sale; no license is inferred from dependency licenses.
- [ ] Direct and transitive dependency licenses are regenerated from the final lock file.
- [ ] Default model license and redistribution behavior are rechecked.
- [ ] Refund/support terms and seller identity are stated on the product page.
- [ ] Checkout works from Morocco and in the target buyer countries.
- [ ] A real low-value purchase/refund test is completed before public promotion.

This checklist is operational guidance, not legal or tax advice.
