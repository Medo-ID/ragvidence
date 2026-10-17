# Release, repository cleanup and website completion

Execution record updated 2026-10-17. Tasks 1–3 are complete. The human Windows
review in task 4 is deferred by the maintainer. PyPI publication and production
installation passed; the GitHub Release page is pending completion. Website work
remains a separate session.

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

The main sequence is **TestPyPI → installed-user review → PyPI → production
installation → website/docs update → website verification → deployment → launch**.
Complete the small CLI cleanup below before the final TestPyPI upload because
the README and user documentation are included in the published distributions.

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

- [ ] Confirm private vulnerability reporting, required CI and release/environment
  access in GitHub. Remote settings need the maintainer's authenticated account;
  local files do not verify them.
- [x] Confirm the chosen version is available on both indexes. The intended
  version is `0.2.0`; keep pyproject/runtime/lock versions aligned.
- [ ] Check each project's Trusted Publisher configuration: owner `Medo-ID`,
  repository `ragvidence`, workflow `release.yml`, and the corresponding
  `testpypi` / `pypi` environment. Check any environment approval requirements.
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

- [ ] Use an isolated installation of the exact TestPyPI wheel, outside both
  repositories, rather than replacing a personal tool installation accidentally.
- [ ] On the available Windows machine, check a fresh terminal, version,
  techniques, verification, a file/folder with spaces or Unicode, question prompt,
  question file, source-only run, and missing/malformed input errors.
- [ ] Generate HTML/JSON/Markdown; open HTML offline and on a narrow screen,
  inspect passages and limitations, and copy/share a synthetic report.
- [ ] Compare two techniques, then repeat with reviewed evidence. Confirm there
  is no invented quality winner for questions without relevance references.
- [ ] If advertising a local-model example, run that example with an identified
  model and record the outcome. Retain the existing bounded real-model evidence;
  do not treat runtime installation as inference-quality proof on every OS.
- [ ] Record version, artifact hash, OS, shell/browser and any observed issues.
  GitHub already supplies automated Windows/macOS execution; this review checks
  usability. A human macOS review is useful when a Mac is available and must not
  be reported as performed otherwise.

Exit: no unresolved release-blocking issue. If fixes change the uploaded package,
return to the candidate process using a fresh version rather than overwriting an
index filename. An isolated prerelease such as `0.2.0rc1` can be used for an early
rehearsal if further package changes are expected, followed by final `0.2.0`.

## 5. Publish to PyPI and create the GitHub release

- [x] Tag the exact TestPyPI-verified release commit as `v0.2.0` under Medo-ID and
  push it intentionally. Human review was explicitly deferred as recorded above.
- [x] Complete full platform verification, PyPI upload and the exact published-wheel
  installation. Run 39012063464 succeeded; GitHub Release creation was skipped.
- [ ] Complete the GitHub Release using the existing tag and the four original
  verified release assets. The implicit skipped-job dependency condition has a
  source fix for future runs; do not retag or repeat a successful package upload.
- [ ] Check the GitHub release contains the intended distributions, checksums
  and provenance; review generated notes against the actual shipped scope.
- [x] Compare the production wheel and source-distribution hashes with the
  TestPyPI candidate. The current workflow rebuilds from the tag; it verifies the
  index wheel against that run's build, so explicitly check the cross-index
  hashes too. Investigate any mismatch before announcing the release.
- [ ] If an upload succeeded and a later job failed, rerun only the failed jobs.
  Do not retag published bytes or rerun a successful upload unnecessarily.

Exit: the production package, post-publication check and GitHub release succeed.

## 6. Confirm production installation and finish the CLI handoff

- [x] Install `ragvidence==0.2.0` from production PyPI in a clean environment;
  confirm version, `ragvi verify`, one own-data run, one comparison and reports.
- [x] Verify optional-runtime installation, README rendering, license metadata,
  source/docs/issues links and ordinary upgrade instructions.
- [x] Update root `instructions.md` with the final version/tag, production URLs,
  release commit, CI links, platform scope, known limits and deferred sponsorship.
  Replace preparation-time availability notes with the observed published status.
- [ ] Keep GitHub documentation links working while the website is undeployed.
  Set the repository About link to the website only when it is live. A later
  package release can update packaged homepage/documentation URLs; that alone
  does not justify rebuilding or replacing the published version.

Exit: a new user can install and use the release, and the website session has an
accurate handoff. All CLI commits continue to use Medo-ID.

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
