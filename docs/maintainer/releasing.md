# Maintainer release procedure

RAGvidence is a free Apache-2.0 CLI. Follow
[the completion checklist](release-and-website-checklist.md) for the ordered CLI
release and separate website work. Maintainer documents are excluded from the
source distribution.

## Prepare the release commit

Keep `pyproject.toml`, `src/ragvidence/__init__.py` and the project entry in `uv.lock`
on the same version. Update the lock after version/dependency changes. Keep the
changelog, docs, capability contracts and third-party notices aligned with the
actual delivered scope.

```bash
uv sync --frozen --dev --all-extras
uv run --no-sync python -m scripts.verify_release --online-install
```

The gate preflights dependencies for four target platforms, lints, runs tests,
checks capability outcomes and bundled assets, builds to `dist/release/`, inspects
wheel/sdist contents and licenses, and exercises isolated core wheel/source and
PDF/semantic-runtime installations. Core tests stay offline; `--online-install`
allows locked package metadata/dependencies from PyPI, with model downloads disabled.
A fully warm resolver cache can run without that flag.

The default outcome directory is ignored `verification/ci/local/`. Use `--output`
with another directory when recording a candidate; do not replace retained
canonical evidence. `tests.json` records actual per-test outcomes and
`capabilities.json` binds claims to required passing contracts.

Start with an empty distribution directory when changing versions. Stale versions
fail inspection. `SHA256SUMS.txt` and `provenance.json` bind artifacts to hashes,
source commit and working-tree status. Build the final candidate from a clean
committed revision; a dirty-tree run is development evidence. Commit as Medo-ID,
push and require hosted verification to pass before publication.

## Platforms and upgrades

`.github/workflows/verify-release.yml` runs the common gate on Ubuntu x64,
Windows x64 and macOS ARM64/Intel with Python 3.12. CI invokes it on main pushes
and pull requests; both publication jobs require the complete matrix. Optional
runtime installation does not prove real-model inference compatibility.

Intel macOS needs ONNX Runtime below 1.24; the semantic extra carries that marker.
The universal lock and `tool.uv.required-environments` protect the four targets.
`.gitattributes` keeps checksum-bound text fixtures on LF. Original input CRLF
characters remain preserved for reviewed source offsets.

CI fetches a checksum-pinned official upgrade baseline and exercises isolated
upgrades, unchanged original artifacts and exports. To repeat it locally:

```bash
uv run --no-sync python -m scripts.fetch_release --index pypi --version 0.1.0 --output .ragvidence-cache/releases --expected-sha256 6dc10ba92245c332292f578591bbc88aab0d5827a1e445292c75fcc5dd5029ee
uv run --no-sync python -m scripts.check_upgrade --old .ragvidence-cache/releases/ragvidence-0.1.0-py3-none-any.whl --candidate-dir dist/release --output verification/ci/upgrade-check.json --online-install
```

## Real-model and manual checks

Use already-downloaded approved files/digests, explicit request limits and a new
outcome path. Keep actual quality outcomes, including valid output that loses
required facts. Do not turn compatibility results into universal accuracy claims.

```bash
HF_HUB_OFFLINE=1 uv run --no-sync python scripts/check_portable_models.py --cache-dir .ragvidence-cache --output verification/ci/model-check.json
uv run --no-sync python scripts/check_portable_transformations.py --model qwen3:8b --expected-digest 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41 --output verification/ci/transform-check.json
```

In PowerShell set `$env:HF_HUB_OFFLINE="1"` instead of the Unix inline assignment.
The transformation check does not install Ollama or pull a model.

For human review, install the exact candidate in an isolated tool environment,
open a fresh terminal outside the repository and use synthetic data. Check
question entry, file/folder runs, missing/malformed inputs, optional runtime errors,
all exports, offline HTML/mobile/print, comparison and reviewed evidence. Record
artifact hash, OS, shell/browser and observed issues. Automated checks do not
substitute for that usability assessment.

## Publish and verify

Confirm both index dashboards trust owner `Medo-ID`, repository `ragvidence`,
workflow `release.yml` and the matching `testpypi` / `pypi` environment. Remote
settings and environment approvals require an authenticated maintainer account.

1. Dispatch **Publish release**, choosing **main** and **target: testpypi** on the
   final release commit. The default `verify` target does not upload.
2. Require the platform matrix, TestPyPI upload and exact published-wheel
   installation to pass. Record the run, revision and distribution hashes.
3. After the candidate review, tag that exact commit as `vVERSION` and push the
   tag intentionally. This triggers production PyPI publication.
4. Require the matrix, PyPI upload, production installation and GitHub Release
   creation to pass. Compare production wheel/sdist hashes to the TestPyPI
   candidate; the workflow rebuilds from the tag rather than promoting an upload.
5. Review release assets, notes, license metadata and index description, then
   test production installation outside the repository.

Only wheel/sdist files enter the index upload directory. Checksums/provenance are
release assets. The published-wheel check downloads the exact project wheel from
the selected index and verifies its SHA against that run's build. Dependencies
use PyPI; TestPyPI is not an unrestricted fallback index.

If package contents change after upload, select a fresh candidate/version; index
filenames cannot be overwritten. If upload succeeded but a later check failed,
rerun failed jobs rather than the successful upload. Never move a published tag
to different bytes. Prerelease tags create prereleases on GitHub. Release
immutability settings must be confirmed separately in the repository dashboard.

If only GitHub Release creation was skipped after a verified PyPI upload, create
the release from the existing tag and attach the original run's `release-assets`
files. Verify the archive digest and both index hashes before attaching them.
Do not rerun the index upload. The release job uses an explicit status check and
requires successful production publication and published-wheel verification so
a skipped TestPyPI ancestor does not suppress it.

Git SSH access can push commits/tags but does not authenticate Actions dispatch.
Use the maintainer's GitHub UI or authenticated CLI to dispatch the workflow.

## Finish

Record actual outcomes in the completion checklist and root `instructions.md`.
The website session uses the exact production release for documentation, samples
and media. Keep working GitHub documentation URLs until the website is live.
See [repository maintenance](repository.md) for public settings and
[sponsorship setup](sponsorship.md) for optional support links.
