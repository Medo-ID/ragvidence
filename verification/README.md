# Local verification output

Maintained tests and fixtures live in `tests/`; repeatable release and model
checks live in `scripts/`. Keep those source files tracked.

Store generated local outcomes under `verification/ci/`. Everything in this
directory except this README is ignored. Logs, JSON outcomes, screenshots, PDFs
and historical run downloads are not required to run, develop or release the CLI.
Delete local outputs when they are no longer useful.

GitHub Actions retains verification output as workflow artifacts according to
the retention settings in `.github/workflows/`. Published package files and
release provenance belong with their corresponding GitHub Release. Assess a
candidate using the checks for its exact commit; historical outcomes do not
validate later changes.

See [contribution guidance](../CONTRIBUTING.md) and
[the release procedure](../docs/releasing.md) for current commands.
