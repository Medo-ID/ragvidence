# Maintainer release procedure

This file is internal and excluded from customer source distributions.

## Before release

1. Recheck the RAGvidence product and package names before every public release. The October 2026 clearance search found no exact-match software or package conflict, but it was not a formal trademark opinion.
2. Replace generic seller/contact references with the legal seller identity and support address used at checkout.
3. Have the proprietary license, refund terms, privacy notice, and checkout terms reviewed for the seller’s jurisdiction and target markets.
4. Confirm every advertised Free and Plus capability exists in the exact delivered build.
5. Update `CHANGELOG.md`, version metadata, lockfile, and dependency notices.
6. Test checkout, payment completion, refund/revocation, download, and activation in PayPal sandbox before live mode.

## Quality gate

```bash
uv sync --frozen --dev
uv run ruff check src tests
uv run pytest
uv run ragvidence verify
uv build
```

Then install the built wheel into an isolated tool environment:

```bash
uv tool install --force dist/ragvidence-0.1.0-py3-none-any.whl
ragvidence health
ragvidence tutorial --root /tmp/ragvidence-release-smoke
```

Inspect wheel and source-archive contents. Neither may include `.env`, workspaces, caches, build directories, maintainer documentation, credentials, or customer data.

## Artifact integrity

Create checksums after the final build:

```bash
sha256sum dist/* > dist/SHA256SUMS.txt
```

Publish the checksum beside the artifacts. Retain the source commit, lockfile, build logs, dependency-license report, and checkout terms used for the release.

## Distribution decision

- Keep the development repository private because it contains the commercial roadmap and future Plus work.
- A public PyPI package is suitable only for the Free build and makes its Python code downloadable and inspectable.
- Keep Plus code out of a public wheel. Deliver it from authenticated storage after verified purchase.
- Do not use a private GitHub release URL as a customer download link; private repository assets require GitHub authorization.
- Do not publish to PyPI until the final package name is checked and reserved.

## Release record

Record the tag, full commit SHA, artifact hashes, test results, build platform, Python version, and the person approving release. Prefer immutable release assets.
