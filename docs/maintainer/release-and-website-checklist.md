# Release, repository cleanup and website completion

Execution record updated 2026-10-18. CLI cleanup, TestPyPI/PyPI publication,
production installation and the GitHub Release are complete. All available
automated CLI release checks passed. Task 4's human Windows review remains
explicitly deferred. Branch/tag protections and private reporting passed; the
completed owner-action section has been removed. The final documentation branch
is blocked by the current Actions allowlist (task 6). Website tasks 7–13 follow
in the separate website session. No CLI feature or publication task remains.

## Starting point

- Release commit: `fba0c92`, annotated tag `v0.2.0`, authored/tagged by Medo-ID.
  [Production run 39012063464](https://github.com/Medo-ID/ragvidence/actions/runs/39012063464)
  passed Linux x64, Windows x64, macOS ARM64/Intel and published-wheel checks.
- Retrieval techniques, evidence evaluation, comparisons and release gates are implemented.
  Generated-answer/citation judging is not included.
- CLI source is public, Apache-2.0, with all included features free.
- Version 0.2.0 is live on both TestPyPI and PyPI. The wheel/source hashes match
  across indexes; root `instructions.md` records the release identities.
- Sponsorship setup is deferred and does not block release or website launch.
- Website work belongs in a later session in `../ragvidence-web`, using root
  `instructions.md`. That repository already has uncommitted changes; preserve
  them and review their intent before making additional changes.

The recorded sequence is **CLI cleanup → TestPyPI → installed-user review
(deferred) → PyPI → production installation → GitHub Release → repository setup**.
Next is **website/docs update → website verification → deployment → launch**.
Do not rebuild or republish the released version for
maintainer-only documentation changes.

## 1. Finish the CLI wording and repository cleanup

- [x] Rewrite README, contributor guidance and usage/technique/comparison guides
  around the current free Apache-2.0 CLI and the decisions users can make with it.
- [x] Provide accurate current-version installation, upgrade and first-use
  instructions. Track actual publication status in the maintainer handoff.
- [x] Make CHANGELOG describe the current update and its capabilities. Preserve
  release tags, published artifacts, checksum-pinned upgrade tests, fixtures and
  original verification evidence.
- [x] Retire redundant design/commercial/milestone plans, consolidate useful
  verification guidance, and repair links/package inclusion. Current user docs
  describe implemented capabilities and their actual limits.
- [x] Review generated logs, captures, caches, temporary files and verification
  directories. Keep maintained scripts/tests and concise supporting evidence;
  remove only confirmed obsolete material. Keep release artifacts and private
  local data out of the source package. Avoid unrelated code refactors here.
- [x] Confirm LICENSE, NOTICE, third-party notices, package URLs, contribution,
  support and security guidance agree with the free public CLI.
Exit: the current documentation is useful, concise and aligned with the CLI.

## 2. Verify and commit the final candidate

- [x] Run documentation/link checks and execute the first-use examples.
- [x] Run the shared release gate for the final cleanup and inspect its outcomes.
  Local results: 395 passing tests, all capability contracts, wheel/source checks
  and three isolated installation modes. Outcomes: `verification/ci/local/`.
- [x] Commit as **Medo-ID <midaghdour@gmail.com>**, push, and require the
  four-platform CI matrix to pass on that exact commit.

Exit: one clean release commit with accurate package documentation and passing CI.
Do not perform further package-content edits between TestPyPI and production
publication without producing and verifying a new candidate.

## 3. Publish the final candidate to TestPyPI

- [x] Verify the workflow's publishing access by successful OIDC uploads to both
  indexes. The maintainer also confirmed reviewing ongoing publishing access.
- [x] Confirm the chosen version is available on both indexes. The intended
  version is `0.2.0`; keep pyproject/runtime/lock versions aligned.
- [x] In GitHub **Actions → Publish release → Run workflow**, select **main**
  and **target: testpypi**. Confirm main still points to the final release commit.
  The default target, `verify`, does not upload anything.
- [x] Wait for the complete platform matrix, TestPyPI upload, and **Install the
  exact published wheel** job. Publication alone is not the completion condition.
- [x] Save the run URL, tested commit, wheel/sdist hashes and results. Inspect the
  TestPyPI description and Apache-2.0 metadata.

The current environment can push through Git SSH but cannot manually dispatch
Actions without an authenticated GitHub session. The maintainer can dispatch
through the UI; monitoring the public run is possible here.

Exit: the final candidate exists on TestPyPI and its published-wheel hash and
installed workflows pass. Dependencies come from PyPI; do not configure TestPyPI
as an unrestricted fallback source for unrelated dependencies.

## 4. Review the candidate as an ordinary user

**Deferred by the maintainer on 2026-10-17; not marked passed.** Automated
Windows/macOS checks passed. The maintainer explicitly chose to proceed to
production publication without this human review. A downloadable synthetic ZIP
is prepared locally at `local-data/ragvidence-0.2.0-manual-check.zip`, with
PowerShell commands, reviewed references and a Linux fixture-check record.

- [ ] Use an isolated installation of the exact production `0.2.0` wheel, outside both
  repositories, rather than replacing a personal tool installation accidentally.
- [ ] On the available Windows machine, check a fresh terminal, version,
  techniques, verification, a file/folder with spaces or Unicode, question prompt,
  question file, source-only run, and missing/malformed input errors.
- [ ] Generate HTML/JSON/Markdown; open HTML offline and on a narrow screen,
  inspect passages and limitations, and copy/share a synthetic report.
- [ ] Compare two techniques, then repeat with reviewed evidence. Confirm there
  is no invented quality winner for questions without relevance references.
- [ ] Record version, artifact hash, OS, shell/browser and any observed issues.
  GitHub already supplies automated Windows/macOS execution; this review checks
  Windows usability. Broader human/model/hardware checks are optional future work.

Exit: record the actual human review and any issues found. If a fix changes the
published package, use a fresh version; do not replace `0.2.0` or move its tag.
This deferred review does not block the website session.

## 5. Publish to PyPI and create the GitHub release

- [x] Tag the exact TestPyPI-verified release commit as `v0.2.0` under Medo-ID and
  push it intentionally. Human review was explicitly deferred as recorded above.
- [x] Complete full platform verification, PyPI upload and the exact published-wheel
  installation. Run 39012063464 succeeded; GitHub Release creation was skipped.
- [x] Complete the [GitHub Release](https://github.com/Medo-ID/ragvidence/releases/tag/v0.2.0)
  manually using the existing tag and the four original verified release assets.
  The implicit skipped-job dependency condition is fixed for future runs; no
  retagging or repeat package upload was needed.
- [x] Download all four release attachments and compare them byte for byte to
  the original production run. Verify GitHub SHA-256 digests, both index hashes,
  the checksum manifest, and provenance's clean source commit. Verify the remote
  tag still resolves to `fba0c92ddaeb414ba8e9f0dea0e0c93f4e9c29f4`.
- [x] Review release notes against the shipped capabilities and limits. The
  release is public, published and not marked as a prerelease. GitHub's automatic
  source-code ZIP/tar archives are separate from the four uploaded assets.
- [x] Compare the production wheel and source-distribution hashes with the
  TestPyPI candidate. The current workflow rebuilds from the tag; it verifies the
  index wheel against that run's build, so explicitly check the cross-index
  hashes too. Investigate any mismatch before announcing the release.
Recovery rule for future releases: if an upload succeeded and a later job failed,
rerun only the failed jobs. Do not retag published bytes or repeat a successful upload.

Exit: the production package, post-publication check and GitHub release succeed.

## 6. Confirm production installation and finish the CLI handoff

- [x] Install `ragvidence==0.2.0` from production PyPI in a clean environment;
  confirm version, `ragvi verify`, one own-data run, one comparison and reports.
- [x] Verify optional-runtime installation, published README content, license
  metadata and source/docs/issues links.
- [x] Update root `instructions.md` with the final version/tag, production URLs,
  release commit, CI links, platform scope, known limits and deferred sponsorship.
  Replace preparation-time availability notes with the observed published status.
- [x] Keep GitHub documentation links working while the website is undeployed.
  The public repository is Apache-2.0 with issues enabled and no website About
  URL. Package documentation links continue to use GitHub. A later release can
  update packaged URLs after the website is live.
- [x] Confirm no temporary verification branch/worktree remains, retain unrelated
  branches and history, and keep personal setup/data/build outputs ignored.
- [x] Prepare the separate website plan below and refresh root `instructions.md`
  with the published release, verified files, current scope and deferred work.
- [x] Complete repository setup: active main-branch protection with all five
  GitHub Actions checks, up-to-date merging, pull requests and no required review
  from another person; active `v*` protection against tag updates/deletion while
  allowing new release tags; private reporting enabled. Public configuration
  verified on 2026-10-18. Bypass lists are not exposed in the public response;
  signed-in setup was confirmed by the maintainer. No destructive test performed.
- [x] Record the maintainer's confirmation of publishing-settings and live PyPI
  visual reviews. Public API checks independently verified the repository rules
  and private reporting; private index settings and browser rendering are human
  confirmations.
- [ ] Restore access to the existing CI actions. Final handoff run
  [39134648119](https://github.com/Medo-ID/ragvidence/actions/runs/39134648119)
  failed at startup with zero test jobs because the repository permits only
  Medo-ID-owned actions. This is a settings failure, not a test result. In
  **Settings → Actions → General → Actions permissions**, select **Allow Medo-ID,
  and select non-Medo-ID, actions and reusable workflows**. Under specified allowed
  actions, add these comma-separated references and save:

  ```text
  actions/checkout@v7, actions/upload-artifact@v7, actions/download-artifact@v8, astral-sh/setup-uv@bec219d24cd3e171d82865faccec33120bb574f4, pypa/gh-action-pypi-publish@release/v1
  ```

  These are the five external action references in the checked-in workflows.
  Keep the branch/tag protections. Do not change workflow token permissions to
  resolve an action-source restriction.
- [ ] After saving that setting, open the final documentation PR from
  `verification/website-handoff-20261018` to `main`. PR creation triggers fresh CI;
  wait for all five required checks, merge, and remove the temporary branch.
  This environment has Git SSH push access but no authenticated GitHub API session
  to create/merge the PR or edit Actions settings.

Exit: automated production journeys pass and the website has an accurate handoff.
No CLI implementation/publication work remains. Complete the two final handoff
items above before declaring the CLI folder closed. The human Windows review is
the only deferred CLI test. Sponsorship, M7 and broader model checks remain optional
future scope. All maintainer commits use Medo-ID; future changes go through a
branch and pull request under the new main protection.

## Deferred website plan

Tasks 7–13 are the next work in `../ragvidence-web` and have not been executed
in this CLI session. Read root `instructions.md` first there, inspect the actual
repository state, and preserve existing work. Task 13's cross-repository link
updates happen after website deployment; they are not unfinished CLI release
work. Host/domain access and final deployment require the maintainer's action in
the website session. Sponsorship is optional and does not block completion.

## 7. Start the separate website session and reconcile its existing changes

- [ ] Open `../ragvidence-web`; read AGENTS.md, README, `docs/maintaining.md`,
  `docs/project-health.md`, and the CLI's updated `instructions.md`.
- [ ] Inspect existing modifications/deletions and preserve their intent. Review
  and checkpoint the existing cleanup separately before mixing in product edits.
  Do not restore deleted design assets or discard unrelated changes blindly.
- [ ] Use the repository's Node 24/npm setup. Read its installed Next.js guides
  before editing framework behavior.
- [ ] Make a content checklist mapped to the published CLI help, capabilities,
  coverage, reports and actual supported input schemas. CLI behavior/docs remain
  the source for technical claims; update website content and its tests together.

Exit: the website work has a reviewed baseline and a concrete content map.

## 8. Update the landing page, product claims and trust pages

- [ ] Rewrite the primary workflow around portable local data → chosen retrieval
  technique/comparison → evidence → terminal/shareable reports.
- [ ] Present one free Apache-2.0 CLI with Install, Source, Contribute and Star.
  Keep copy focused on current capabilities and the user's workflow.
- [ ] Update `src/app/page.tsx`, `src/components/product-sections.tsx`, shared
  navigation/footer, releases, privacy/terms/security pages, metadata and JSON-LD.
  Distinguish the CLI license from the website's own rights and third-party assets.
- [ ] Keep the diagnostic scope accurate: no production-system modification,
  universal best-technique promise, generated-answer judging or answer-judging capability.
  State tested OS/architecture/Python scope and precise local-model requirements.
- [ ] Keep sponsorship optional. Add its external link only after a working
  destination is supplied and verified.

Exit: all visible copy and machine-readable metadata describe the shipped product.

## 9. Update the website documentation and examples

- [ ] Update `src/lib/docs.ts`, the doc version badge and generated navigation /
  search index for the published release. Cover installation/upgrade, supported
  file schemas, source/questions/reviewed modes, technique requirements, imports,
  comparisons/resume, exports, privacy, local models and troubleshooting.
- [ ] Run documented commands against the installed production release using
  synthetic data. Check copied commands, optional extras and Windows-compatible
  guidance. Explain that reviewed evidence is needed for scored relevance.
- [ ] Make current docs focus on the current release. Keep any useful historical
  release entry/license record clearly separate; avoid old-version commentary
  throughout the main tutorial and landing page.
- [ ] Update license download routes, release links, site verification expectations
  and tests. Remove obsolete assets only after checking references. Do not rename
  an old license file and present its contents as the new release's license.
- [ ] Align `AGENTS.md`, README and maintenance guidance with the current CLI's
  capabilities and verified examples.

Exit: every published example works and current docs agree with the actual wheel.

## 10. Regenerate the sample report and demonstration media

- [ ] Generate the sample report with the exact production release and synthetic
  inputs. Prefer an own-data technique/comparison example that explains the core
  product; keep the fictional tutorial only where it is useful and identified.
- [ ] Update terminal demo, screenshots, video/poster and captions as needed.
  Review `scripts/record-walkthrough.mjs`, whose current default names an old wheel.
- [ ] Record package version/hash, commands, configuration, model identity when
  used, source/report hashes and actual question-level outcomes in provenance.
- [ ] Update old result percentages only from real new outputs. Preserve report
  notices; do not hand-edit authoritative report results or imply a general gain.
- [ ] Verify shared HTML offline, long/Unicode content, mobile layout, print,
  video encodings and reduced-motion behavior.

Exit: public examples are reproducible evidence for the advertised release.

## 11. Pass the website quality gate

- [ ] Resolve the two recorded reduced-motion video failures in
  `tests/browser/site.spec.ts`, then rerun them. Confirm their current status
  rather than treating the earlier report as a fresh test result.
- [ ] Run `npm ci` and `npm run verify`: lint, TypeScript, production build,
  HTTP/site verification, verifier tests, browser tests and production audit.
- [ ] Verify the normal Turbopack build on a capable host/CI. A restricted-host
  Webpack fallback is not evidence that the normal production build passed.
- [ ] Check keyboard navigation, focus, menus, search, copy failures, responsive
  layout, reduced motion, report downloads and browser console errors.
- [ ] Review production/development dependency findings and update
  `docs/project-health.md` with current results. Update tests enforcing obsolete
  product content; preserve meaningful accessibility and behavior coverage.
- [ ] Review the diff, commit as Medo-ID, push and require website CI to pass.

Exit: the full production website gate is green with no concealed test failures.

## 12. Deploy a preview, then production

- [ ] Select the intended Next.js host using Node 24 and the normal build/start
  flow. Check that deployed content matches the verified website commit.
- [ ] Verify the preview URL using `RAGVIDENCE_SITE_URL=PREVIEW_URL npm run verify:site`
  and browser checks. Confirm canonical URLs, metadata, robots/sitemap, security
  headers, static assets and links; keep previews out of search indexing as needed.
- [ ] Deploy the reviewed result as the final separately authorized website
  action. Configure `ragvidence.medo-id.com` and the host-supplied DNS records.
- [ ] Verify production HTTPS, redirects, canonical domain, docs/search, copy
  controls, media, sample reports and CLI/PyPI/GitHub links from an ordinary browser.
  Record the deployed commit and an available rollback path.

Exit: the public domain serves the verified site and live checks pass.

## 13. Close the work and announce

- [ ] Update repository About/homepage links and final release notes to point to
  live verified destinations. Do not change immutable published artifacts.
- [ ] Ensure both repositories have clean, intentional working trees, no leftover
  temporary verification branches/worktrees, and no accidentally staged outputs.
  Preserve unrelated branches and original release history.
- [ ] Confirm Install → own data → report → docs → contribute works end to end.
- [ ] Record completed steps, release/site commits, live URLs and remaining
  optional follow-ups. Announce only supported shipped functionality.
- [ ] Sponsorship can follow later using `docs/maintainer/sponsorship.md`. Once
  approved, verify the URL, add `.github/FUNDING.yml` and the website link, update
  affected content/tests, and check both links. It remains optional and unlocks
  no CLI features.

Done means: production CLI installs and verifies, current docs are accurate, the
website is live and passes its gate, both repositories are tidy, and the product
is consistently presented as a free diagnostic/evaluation CLI. Answer judging is outside this release;
sponsorship remains optional and must not be advertised as configured.

## External procedure references

- [GitHub manual workflow dispatch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
- [Why uploaded filenames cannot be reused](https://pypi.org/help/#file-name-reuse)

Confirm index/dashboard state when executing. If package bytes must change after
an upload, use a fresh candidate/version; deleting an upload does not make its
filename reusable. Keep the TestPyPI-tested candidate aligned with production.
