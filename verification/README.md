# Verification evidence

Maintained test code lives in `tests/`; repeatable release/model checks live in
`scripts/`. Keep those sources and fixtures even when their generated outputs
are no longer needed.

Retained evidence:

- `portable-m8/github/38921470479/`: complete passing Linux, Windows and macOS
  ARM64/Intel test, installation and upgrade outcomes, with run/job identities.
- `portable-m8/github/run-history.json`: run outcomes and diagnostic corrections.
- `portable-m8/model-check.json` and `transform-check.json`: identified real-model
  checks, including observed quality failures.
- The other `portable-m8/` JSON files: the corresponding local gate, contracts,
  upgrade results and source/readiness hash records. Preserve the packet together.

These files describe their recorded revisions. Require passing hosted checks on
the actual final release commit as described in
[the release procedure](../docs/maintainer/releasing.md).

Store fresh local outputs under ignored `verification/ci/`; GitHub retains each
run's artifacts according to workflow retention. Keep only useful canonical proof
in Git. Superseded intermediate checkpoints and duplicate local runs are not
required to execute tests, build the CLI or assess the retained passing result.
