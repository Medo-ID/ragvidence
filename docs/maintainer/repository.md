# Maintain the public repository

RAGvidence is a fully free Apache-2.0 CLI. Keep public documentation focused on
the current release, how to use it and the evidence users can obtain.

## Source and contributions

The CLI source is `Medo-ID/ragvidence`. Contribution setup and validation are in
[CONTRIBUTING.md](../../CONTRIBUTING.md). Keep issue/PR templates, support and
security reporting links usable. Use synthetic data in public examples and
retain software, font and model notices with their corresponding artifacts.

Use **Medo-ID <midaghdour@gmail.com>** for maintainer commits. Preserve unrelated
working-tree changes, branches and release tags. Review generated artifacts and
staged changes before committing. Keep private data, credentials and model caches
out of the repository and distributions.

## GitHub settings

Confirm required passing CI, branch/merge protections, private vulnerability
reporting and publishing-environment access using the maintainer's authenticated
account. Source configuration does not establish that remote settings are active.
Test jobs have read-only repository permissions; OIDC upload permission belongs
to publishing jobs.

## Releases and website

Follow [the release procedure](releasing.md) and
[the completion checklist](release-and-website-checklist.md). Keep current user
documentation concise; raw verification outcomes describe the actual tested
revision and must not be edited to imply a newer check passed.

The website is maintained separately in `../ragvidence-web`. Use root
`instructions.md` for its technical handoff. Update public availability claims and
demos against the actual production release. Verify a website URL before making
it the primary package/repository destination.

Sponsorship is optional and currently unconfigured. Its later setup is described
in [sponsorship.md](sponsorship.md); it is not a release requirement.
