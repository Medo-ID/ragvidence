# Public Apache-2.0 transition plan

This is a plan for the existing private `Medo-ID/ragvidence` repository. No commit,
push, visibility change, release edit or publication is performed by writing it.
The CLI remains completely free; sponsorship is voluntary and unlocks no features.
The website stays separate until its own update session.

## 1. Finish local M8

Keep the candidate uncommitted until the maintainer changes that instruction.
Complete the shared gate, real model compatibility against the actual lock,
upgrade/legacy checks, package inspection and the website handoff. Keep OS execution
and human usability marked pending until actually performed. Do not call M8 fully
verified while Windows/macOS jobs are pending.

## 2. Review what will become public

Prefer keeping the existing repository name, package, tags and URLs. Review the
whole available Git history and all branches for secrets, private source/customer
data and material not intended for publication. Review GitHub release attachments,
Actions history/logs/artifacts and issue content as well: local archive inspection
does not cover those surfaces. Verify rights to license included code and preserve
third-party/model/font notices. Commit author names alone are not a license audit.
If sensitive history is found, revoke any affected credentials and discuss cleanup
or a clean public repository before changing visibility. Do not rewrite history,
delete releases or expose the repository as an incidental implementation step.

## 3. Resolve the hosted-test sequencing

GitHub Actions needs a repository revision; it cannot test this uncommitted disk
state directly. Ask the maintainer whether a temporary test branch commit is an
allowed exception, keeping main and release tags unchanged until all jobs pass.
Without that exception, finish local verification and stop before the hosted run.

Use the maintainer's normal authenticated GitHub session/CLI. SSH Git read access
is not an Actions API login. Push only the specifically approved verification
branch and use a verification-only PR workflow or direct dispatch once the new
workflow exists on the default branch. Do not use the current old remote release
workflow, whose manual event publishes to TestPyPI.

Private repositories can run the matrix using their available Actions minutes;
public visibility is not required for Windows/macOS checks. Require Linux x64,
Windows x64, macOS ARM64 and Intel on Python 3.12 to pass, then review human CLI
usability on available real machines. Preserve failed runs and fixes honestly.

## 4. Prepare contributors and optional sponsorship

Before announcing the public repository, add CONTRIBUTING.md with local setup,
architecture boundaries, synthetic fixture policy and meaningful test requirements;
provide issue/PR guidance, support and a private vulnerability-report route.
Require passing checks for changes and review outside contributions before merging.
Ensure public pull-request checks receive no publishing credentials.

Select a real sponsor/donation destination with the maintainer. GitHub Sponsors
onboarding/eligibility must be checked for the maintainer's account; an external
supported funding link is another option. Only then add `.github/FUNDING.yml` and
a website button. Do not invent URLs, require donations, gate capabilities, promise
support SLAs or describe payments as tax-deductible charitable contributions.
Stars, issues, pull requests and sharing are welcome independently of sponsorship.

## 5. Public release

After the maintainer reviews the exposure audit and authorizes publication, make
the existing repository public. Recheck security/reporting settings, branch rules
and the intended public download/source links. Give the maintainer a final review
before the visibility action, since it exposes history and Actions logs.

Keep v0.1.0 and its published artifacts intact under their historical terms.
Publish 0.2.0 with Apache-2.0 metadata, LICENSE and NOTICE. Do not overwrite old
PyPI versions or silently retag old releases. Verify Trusted Publisher settings
against the same owner/repository/workflow/environments, publish the tested
candidate to TestPyPI deliberately, then publish the version-tagged release to
PyPI and verify the index wheel against the candidate SHA. Only advance the main
branch/release tags in the order specifically approved by the maintainer.

## 6. Website and announcement

Use root instructions.md in the later website session. Remove Free/Plus messaging;
show the actual free CLI, supported inputs/techniques, reviewed-evidence limits,
verified OS outcomes, Source / Contribute / Star links and optional sponsorship.
Do not announce portable commands against the old 0.1.0 installation. Match demos,
reports, source commit and package version to the tested published release.

References: GitHub's repository visibility documentation, hosted-runner reference,
manual-workflow guide and sponsor-button guide; the Apache-2.0 license. These do
not replace checking this repository's actual remote settings and contents.
