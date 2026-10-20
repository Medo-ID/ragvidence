# Release procedure

## Prepare and validate

Keep the version in `pyproject.toml`, `src/ragvidence/__init__.py` and the project
entry in `uv.lock` aligned. Update the changelog, documentation, capability
contracts and third-party notices when the delivered behavior changes. Ordinary
setup uses the frozen dependency lock:

```bash
uv sync --frozen --dev --all-extras
uv run --no-sync python -m scripts.verify_release --online-install
```

The shared gate checks dependency availability for the four supported targets,
lints source, runs tests and capability contracts, verifies bundled assets,
builds distributions and exercises isolated installed wheel/source/optional-extra
journeys. Unit tests block external network access. `--online-install` allows
package metadata and dependencies to be fetched; it does not download models.

Generated outcomes go to ignored `verification/ci/local/`; distributions go to
ignored `dist/release/`. Start with an empty distribution directory for each
candidate. Use `--output` and `--dist` to select other locations. Review
`checks.json`, `tests.json`, capability outcomes and installation results,
including failures.

Build final release artifacts from a clean committed revision and require CI for
that exact commit. `SHA256SUMS.txt` and `provenance.json` bind package files to
their source identity and digests. The release workflow repeats the gate on
Linux x64, Windows x64 and macOS ARM64/Intel with Python 3.12. Optional runtime
installation alone does not establish real-model compatibility.

## Upgrade and manual checks

The workflow downloads a checksum-pinned official baseline and checks isolated
upgrades without changing the user's global installation or existing artifacts.
To reproduce that check after building the candidate:

```bash
uv run --no-sync python -m scripts.fetch_release --index pypi --version 0.1.0 --output .ragvidence-cache/releases --expected-sha256 6dc10ba92245c332292f578591bbc88aab0d5827a1e445292c75fcc5dd5029ee
uv run --no-sync python -m scripts.check_upgrade --old .ragvidence-cache/releases/ragvidence-0.1.0-py3-none-any.whl --candidate-dir dist/release --output verification/ci/upgrade-check.json --online-install
```

`.gitattributes` preserves LF for checksum-bound bundled fixtures on all platforms.
Do not normalize user source text or reviewed offsets while preparing a release.

For a human usability check, install the candidate outside the checkout, open a
fresh terminal and use synthetic inputs. Check question entry, paths with spaces
and Unicode, supported formats, missing/malformed inputs, optional-runtime
errors, reviewed evidence, comparisons, and all report exports. Open HTML offline,
resize it and check print output. Record OS/architecture, shell, browser, package
hash and actual failures. Automated checks do not replace this review.

Real-model checks are opt-in tools in `scripts/check_portable_models.py` and
`scripts/check_portable_transformations.py`; inspect their help and provide the
required local model files or service and pinned identity. Keep model weights,
provider settings, prompts and raw outcomes local. Record quality failures as
well as compatibility results, without claiming universal model support.

## Publish and verify

Configure PyPI and TestPyPI Trusted Publishers for this repository's `release.yml`
workflow and its matching `pypi` and `testpypi` environments. Check environment
permissions, required approvals, tag protection and the repository's Actions
allowlist, including nested actions used by the publisher.

1. Dispatch **Publish release** on the final reviewed branch, selecting
   `target: testpypi`. The default `verify` target performs no upload.
2. Require all supported-platform checks, TestPyPI publication and installation
   of the exact published wheel to pass. Record candidate and package hashes.
3. After reviewing the candidate, tag its exact commit as `vVERSION` and push
   that new tag. The tag workflow publishes to production PyPI.
4. Require production publication, exact published-wheel installation and GitHub
   Release creation to pass. Compare package hashes with the tested candidate.
5. Inspect release assets, metadata and notices, then install and verify the
   production package from an unrelated folder.

Only wheel and source-distribution files enter the index upload directory.
Checksums and provenance are GitHub Release assets. The published-wheel check
compares index bytes with the candidate; dependencies resolve from PyPI.

Published filenames cannot be overwritten. Package changes after publication
need a new version. Never move a published tag. If an upload succeeded but a
later job failed, rerun failed jobs rather than repeating the successful upload.
If only GitHub Release creation failed, attach the original verified run's
assets to the existing tag instead of rebuilding or republishing the package.
