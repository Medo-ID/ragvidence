# Public Apache-2.0 transition record

The maintainer made `Medo-ID/ragvidence` public during M8. The CLI is completely
free; optional sponsorship unlocks no features. The website remains a separate
project/session, using root `instructions.md` as its handoff.

## Completed foundation

- M8 was committed and pushed as `16d2557`, authored by Medo-ID, before this
  public-release preparation began.
- Hosted run 38921470479 passed 395 tests and installed wheel/source/optional-runtime
  plus actual 0.1.0 upgrade journeys on Linux x64, Windows x64, Mac ARM64 and Intel.
- The temporary verification branch/worktree were removed. No PR was created or
  merged; the final M8 main commit retains the evidence and fixes.
- The 0.2.0 source declares Apache-2.0, includes LICENSE/NOTICE and third-party
  notices, and has no paid-tier, account or activation gate.

## Public-release preparation

Contribution guidance, synthetic-data bug/proposal forms and a PR template are
added. Public package metadata points to the GitHub source/docs/issues until the
separate website is ready. User documentation follows the actual portable workflow
and describes complete source/prompt content in exports accurately.

The maintainer explicitly deferred sponsorship configuration. No FUNDING file or
active payment link is created. See [sponsorship setup](sponsorship.md) for official
GitHub onboarding/custom-amount instructions. Stars, issue reports, code and docs
contributions are welcome without payment.

## Maintainer checks before announcing

Review public history/branches, release attachments and old Actions logs/artifacts
for anything not intended for publication. Local wheel inspection does not audit
those remote surfaces. Verify contribution rights and preserve third-party/model/
font notices. Do not rewrite history or remove existing releases incidentally.

Review repository settings for private vulnerability reporting, branch protections,
merge review and required passing CI. Public test jobs have read-only repository
permissions and receive no publishing credentials. Remote settings require the
maintainer's authenticated GitHub account; this source cannot claim they are set.

Keep v0.1.0 and its published artifacts intact under historical terms. The new
Apache-2.0 declaration describes 0.2.0 and subsequent source releases, without
silently relabeling old packages or the separate website's code/assets.

## Publication

Build and validate the final public-release commit with the shared release gate.
Confirm the existing PyPI/TestPyPI Trusted Publishers match owner `Medo-ID`, repo
`ragvidence`, workflow `release.yml` and the respective environment names.

Use **Publish release → target: testpypi** on the final main revision to publish
intentionally to TestPyPI. The default target is verify-only. All platform gates
must pass first. The post-publication check fetches only the project wheel from
that index and requires its SHA to match the built candidate; dependencies resolve
from PyPI under the exported lock constraints.

After TestPyPI passes and production publication is authorized, tag that exact
revision as `v0.2.0` and push the tag. The existing production pipeline repeats
all gates before PyPI publication and verifies the published wheel afterward.
Do not overwrite index versions or retag published bytes. SSH Git access can push
a tag; manual workflow dispatch needs an authenticated Actions session. No new
package was published by M8 or by writing this release-preparation documentation.

Update the later website session with the actual live version and URLs only after
publication. Do not demonstrate portable commands against a 0.1.0 installation.
