# Public-release preparation evidence

The local shared gate passed for the public-release preparation on 2026-10-16:

```bash
uv run --no-sync python -m scripts.verify_release --online-install --output verification/public-release
```

`tests.json` records 395 passing tests with no skipped tests. `capabilities.json`
binds technique/loader claims to those outcomes. `checks.json` retains dependency
preflights, build inspection, artifact hashes and three isolated installed-package
journeys (core wheel, source distribution, PDF/semantic-runtime wheel).

This is Linux development evidence from the working tree based on `16d2557`;
the recorded source identity explicitly reports that tree as dirty. A clean
committed revision must pass hosted CI before publication. The earlier complete
four-platform M8 run is retained separately under `verification/portable-m8/`.
These results do not claim that a package was published, remote repository/index
settings were verified, or a human performed the manual usability review.
