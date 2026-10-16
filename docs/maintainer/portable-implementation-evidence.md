# Capability and verification evidence

This document maps implemented behavior to retained checks. Raw outcome files
identify their tested revision; a successful historical run does not validate
later changes. Use the latest passing CI run for the release candidate.

## Behavior contracts

`scripts/capability_contracts.json` maps each advertised technique/loader to
positive, adverse and command-to-report tests. The shared release gate records
per-test outcomes and rejects absent, skipped or failing required contracts.

The contracts cover ranked retrieval/fusion, splitting/parent expansion,
original-span scoring, filters, MMR, bounded query transformations, compression,
context budgets, imported results, loaders and report journeys. Synthetic
providers establish adapter contracts rather than real-model quality.

Core tests block external sockets. Marked local HTTP fixtures may use loopback.
Bundled `ragvi verify` checks deterministic installation assets without model
access. See [contribution guidance](../../CONTRIBUTING.md) for focused validation.

## Installed-package and platform checks

[Run 38924470360](https://github.com/Medo-ID/ragvidence/actions/runs/38924470360)
passed the public-preparation commit `b6d60ba` on Linux x64, Windows x64,
macOS ARM64 and macOS Intel, Python 3.12. Each target executes the shared gate and
an isolated upgrade check. A later release commit must pass its own run.

Retained raw platform outcomes from
[run 38921470479](https://github.com/Medo-ID/ragvidence/actions/runs/38921470479)
are under `verification/portable-m8/github/38921470479/`. That run records
395 passing tests per platform, installed wheel/source/optional-runtime journeys,
and upgrades. Earlier attempts and failure outcomes remain in the run history.

Installed journeys cover unrelated customer folders, Unicode/space paths,
source-only/questions/reviewed modes, all report formats, structured inputs,
metadata scopes, compression, imports, comparisons/resume, unchanged source files,
verification and the tutorial. Separate temporary tool/bin directories keep
personal global installations unchanged.

[Local preparation outcomes](../../verification/public-release/checks.json) and
[per-test results](../../verification/public-release/tests.json) report a dirty
working tree explicitly; they are development evidence rather than a clean
release commit's identity.

## Upgrade integrity

[Upgrade outcomes](../../verification/portable-m8/upgrade.json) use a
checksum-pinned official baseline wheel. The checker creates source artifacts,
upgrades only an isolated tool environment, verifies the original artifacts remain
unchanged, exports all report formats and exercises current commands. Reading
an artifact does not retroactively supply modern span/hash validation; rerun an
experiment when those guarantees are needed.

## Real-model checks

[Cached-model outcomes](../../verification/portable-m8/model-check.json) identify
BGE-small/MiniLM embedding and Xenova MiniLM reranker files, ONNX Runtime identity,
reviewed runs, budgets, MMR, compression, repeated comparisons and validated resume
on Linux. These establish compatibility for those files and examples.

[Local transformation outcomes](../../verification/portable-m8/transform-check.json)
record two bounded Qwen3:8b calls with a checked model digest. Compatibility
passed; the compression output still lost both required facts. Preserve that
quality failure. Valid output structure is not proof of useful evidence selection.

A model name alone does not pin every runtime revision. Do not extend these
specific checks to all languages, models, corpora, hardware or OS combinations.

## Release gates and limits

The shared gate checks target dependency availability, lint, tests/contracts,
bundled fixtures, distribution metadata/assets/licenses and isolated installations.
The release workflow requires the full platform matrix before uploading. Its
published-wheel check verifies index bytes against that run's candidate.

Human usability review, remote Trusted Publisher/environment settings and actual
publication are separate checks. A passing test suite does not establish them.
See [releasing.md](releasing.md) and [the completion checklist](release-and-website-checklist.md).
