# Maintainer release procedure

This file is internal and excluded from source distributions. Version 0.2.0 is a
free Apache-2.0 CLI; all included features require no account or activation.
There is no paid build, entitlement server or checkout requirement. The separate
website and historical 0.1.0 artifacts retain their existing licensing status.

## Prepare a candidate

1. Keep `pyproject.toml`, `src/ragvidence/__init__.py` and the project record in
   `uv.lock` on the same version. Run `uv lock` after changing it.
2. Update the changelog, capability contracts, docs and third-party notices for the
   exact delivered scope. M7 answer/citation/abstention judging remains deferred.
3. Run the shared gate from this repository:

```bash
uv sync --frozen --dev --all-extras
uv run --no-sync python -m scripts.verify_release --online-install
```

The gate records actual per-test outcomes in `verification/portable-m8/tests.json`
and binds each advertised technique/loader to positive, adverse and workflow
contracts in `capabilities.json`. A missing, skipped or failed referenced contract
cannot count as passed. Core pytest blocks external sockets; explicitly marked
HTTP fixtures allow loopback only. Synthetic adapters do not count as real models.

The same gate preflights wheel availability for all four target platforms without
installing their binaries, lints, runs bundled `ragvi verify`, builds to **dist/release/**,
checks exact wheel/sdist contents and license metadata, and exercises isolated core
wheel, core source and PDF/semantic-runtime installations from unrelated data
folders. Installations use exported `uv.lock` constraints with isolated temporary tool/bin
directories. Fresh runners pass `--online-install` to resolve package metadata and
fetch locked dependencies from PyPI. A frozen sync downloads wheel URLs but does
not necessarily populate the simple-index metadata needed by the resolver.
With a fully warm metadata cache, omit that flag for `uv tool install --offline`.
Unit tests and model inference remain offline in both modes.
The checks do not replace a person's global CLI. They cover all report formats,
reviewed spans, imports, comparisons/resume, Unicode/space paths and read-only data.
Installing optional runtimes is not a model-inference quality check.

Use an empty release output directory when changing versions: the artifact checker
rejects stale distribution versions rather than accidentally publishing them.
`SHA256SUMS.txt` and `provenance.json` bind inspected artifacts to source commit,
working-tree status and hashes. A dirty-tree run is development evidence; build
again from the committed candidate before tagging it. Never distribute local
credentials, reports, caches, customer data or maintainer planning documents.

## Compatibility and real models

The reusable and directly dispatchable `verify-release.yml` runs on Ubuntu x64, Windows x64, macOS ARM64 and
macOS Intel, all on Python 3.12. CI runs on main pushes and pull requests; both
publication jobs depend on the **whole** matrix succeeding. `.gitattributes` keeps
checksum-bound fixtures on LF across platforms. Actions retain outcomes/logs for
failures too. No configured runner or skipped job counts as a passing platform.
Intel macOS needs ONNX Runtime below 1.24; the published semantic extra carries
that marker constraint. `tool.uv.required-environments` protects all four targets
when updating the lock. The current universal lock selects 1.23.2; real Linux
model checks must use that runtime too. Dependency preflight is not OS execution.
The local preparation run is Linux only; inspect the first GitHub run before
claiming Windows/macOS support. The matrix does not cover Windows/Linux ARM,
other Python versions, every OS version or every model/hardware combination.

CI downloads **only** the official published 0.1.0 wheel, verifies its pinned SHA,
and exercises an isolated upgrade with unchanged old artifacts and all old export
formats. Run that check locally using:

```bash
uv run --no-sync python -m scripts.fetch_release --index pypi --version 0.1.0 --output .ragvidence-cache/releases --expected-sha256 6dc10ba92245c332292f578591bbc88aab0d5827a1e445292c75fcc5dd5029ee
uv run --no-sync python -m scripts.check_upgrade --old .ragvidence-cache/releases/ragvidence-0.1.0-py3-none-any.whl --candidate-dir dist/release --output verification/portable-m8/upgrade.json
```

Old runs/evaluations can be inspected/exported with their legacy provenance.
Do not claim that reading them retroactively supplies modern hash/span validation;
rerun experiments for modern validated evaluations. Old evaluation hashes were not
stable across all process hash seeds. Preserve old workspaces and create fresh runs.

Real-model checks are separate and make actual model/file identities visible:

```bash
HF_HUB_OFFLINE=1 uv run --no-sync python scripts/check_portable_models.py --cache-dir .ragvidence-cache --output verification/portable-m8/model-check.json
uv run --no-sync python scripts/check_portable_transformations.py --model qwen3:8b --expected-digest 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41 --output verification/portable-m8/transform-check.json
```

For Windows, set `HF_HUB_OFFLINE=1` using PowerShell's `$env:HF_HUB_OFFLINE="1"`
instead of the Unix inline assignment. Supply already-downloaded approved models;
the transformation check does not install Ollama or pull a model. Its two calls
have explicit limits. Compatibility can pass while reviewed quality fails: retain
that outcome. Never claim that a local model check establishes universal accuracy,
multilingual quality or remote-provider/model compatibility. Mutable model tags
and user-selected endpoints are not pinned by a name alone.

## Manual user check

Perform this on the actual Windows machine (ordinary user shell, outside the repo),
and on a Mac when available. GitHub automates regression checks; this check judges
whether the product is understandable. Use a disposable folder with a small real
or synthetic manual and a separate questions file.

1. Install the exact candidate wheel with `uv tool install --python 3.12 PATH_TO_WHEEL`.
   If replacing an existing tool, preserve any needed version and use `--reinstall`
   deliberately. This manual command affects that user's tool environment.
2. Open a fresh terminal; run `ragvi --version`, `ragvi techniques`, `ragvi verify`.
3. Run `ragvi bm25 ./manual.txt` and answer the question prompt. Confirm the terminal
   text explains unscored inspection and prints a usable HTML report path.
4. Run `ragvi bm25 ./manual.txt --questions ./questions.txt --format html --format json --format markdown`.
   Open HTML in a browser with the network disabled. Check navigation, narrow-window
   readability, long/Unicode content, exact passages, limitations and export paths.
   Share a **synthetic** report to another folder/machine and open it there.
5. Run `ragvi compare-data ./manual.txt --questions ./questions.txt --techniques bm25,parent-child`.
   Confirm no invented quality winner without reviewed labels; optionally repeat
   with the documented reviewed-span fixture and check gains/losses in each export.
6. Check a missing input, malformed file, unsupported file, missing optional extra,
   existing output, and `--no-input`. Errors should provide a useful next step.
7. Optionally use a local Ollama embedding/chat model with an explicit `.env` file
   and the advanced-technique guide. Check its provider disclosure and failure
   handling; record model digest, OS/architecture and any invalid output.

Record artifact SHA, OS/architecture, shell, terminal, browser and observed issues.
Manual usability is not automatically marked passed by the unit suite.

## Existing publication flow

The package already exists on PyPI/TestPyPI. Keep the current project and Trusted
Publisher identity; this is an update, not a new package registration. Confirm in
both index dashboards that the GitHub owner/repository, **release.yml** workflow
and `testpypi`/`pypi` environment names match. Local files cannot verify remote
publisher/environment settings or branch protections.

- Manual **Publish release** dispatch defaults to **verify** and publishes nothing.
- Selecting **testpypi** runs every platform gate, then publishes the canonical
  Ubuntu-built wheel/sdist using Trusted Publishing to TestPyPI.
- A pushed **vVERSION** tag must match all three version declarations. After the
  whole matrix succeeds, it publishes to PyPI using Trusted Publishing.
- Publication jobs receive OIDC permission; tests do not. Only wheel/sdist files
  enter the PyPI upload directory. Checksums and source provenance go to release assets.
- After publication, `check_published` fetches only the project's wheel from the
  selected official index, requires its SHA to match the built candidate, and
  repeats installation journeys. Dependencies use the normal PyPI-populated cache;
  TestPyPI is never added as an unrestricted dependency fallback index.
- A GitHub release is created after PyPI and the published-wheel check pass.
  Alpha/beta/rc tags are marked prereleases. GitHub release immutability depends on
  repository settings; the workflow does not enable it by itself.

If post-publication metadata is delayed, rerun the failed installation job once it
is visible. If publication succeeded but a later job failed, rerun failed jobs,
not the whole upload. Index versions cannot be overwritten. Never retag an already
published version to different bytes. Tagging/pushing/publishing is a separate
maintainer action; preparing these files performs none of those actions.

## Website handoff

Use root `instructions.md` in the later `../ragvidence-web` session. Replace the old
Free/Plus messaging with one free CLI and optional user-chosen sponsorship. Verify
live package version and actual platform outcomes before changing public claims.
Do not fabricate a donation destination or relabel the website's license.


## GitHub execution before the release commit

Hosted runners cannot see the local uncommitted working tree. The source and
workflow under test must be available at a GitHub branch/tag revision. A temporary
test branch still requires a commit and push; obtain the maintainer's exception if
they have instructed that no commit be created before hosted checks. Do not run an
old revision and report its result as M8 verification. The current remote workflow
at preparation time is older and manual dispatch publishes to TestPyPI: do not use
it for verification-only requests.

SSH Git access does not itself authenticate Actions API dispatch. At the last
local audit, SSH read access succeeded, but there was no `gh` installation/login,
GitHub API token or connected GitHub app. Authentication should use the normal
GitHub CLI/device flow on the maintainer's machine; never paste credentials in an
issue, command log or chat. After the reviewed test revision is available, run the
direct **Portable release verification** workflow on that branch. This workflow
has no publication jobs. Its first `workflow_dispatch` entry must already exist on
the default branch to use GitHub's manual dispatch interface; a test PR against
main is an alternative trigger for the same verification-only jobs. Pushing an
approved branch named `verification/...` also triggers the CI matrix directly,
using SSH Git authentication without an Actions API dispatch. This still requires
the explicit no-commit exception. A public repository's run outcomes can then be
read without an API login, subject to GitHub access/rate limits.


## Verified M8 candidate

All four jobs in run 38921470479 passed at revision
42e774974e0ebf8a880f33f0aded9f587d22f40c: 395 tests per platform, clean source
identities, wheel/source/optional-runtime installations and actual 0.1.0 upgrades.
Per-platform outcomes are retained under verification/portable-m8/github/38921470479.
The user authorized temporary verification commits and their removal, followed by
one M8 commit on main as Medo-ID before public-release preparation. GitHub's branch
banner was a pull-request suggestion; no PR was opened or merged for verification.
The repository is now public. Publication and sponsorship configuration follow as
a separate release-preparation phase; no package was published by these CI runs.
