"""One portable release gate shared by local verification, CI and publishing."""

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

from scripts.check_capabilities import check as check_capabilities
from scripts.check_distributions import check as check_distributions
from scripts.check_portable_install import check_install
from scripts.release_metadata import ROOT, distributions, git_identity, release_version


def verify(
    output: Path, dist: Path, tag: str | None = None, *, online_install: bool = False
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    version = release_version()
    if tag is not None and tag != f"v{version}":
        raise ValueError("Tag must match package, runtime and lockfile versions")
    record = {
        "schema_version": 1,
        "version": version,
        "platform": platform.system(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "source": git_identity(),
        "status": "running",
        "checks": [],
    }
    env = {**os.environ, "PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1"}

    def command(name, argv):
        start = time.monotonic()
        with (output / f"{name}.log").open("w", encoding="utf-8") as stream:
            result = subprocess.run(
                argv, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT
            )
        record["checks"].append(
            {
                "name": name,
                "status": "passed" if result.returncode == 0 else "failed",
                "seconds": time.monotonic() - start,
            }
        )
        if result.returncode:
            log = (output / f"{name}.log").read_text(encoding="utf-8", errors="replace")
            tail = "\n".join(log.splitlines()[-80:])[-12000:]
            print(tail, file=sys.stderr)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                # Public check annotations keep hosted-only failures diagnosable
                # when downloading the retained log artifact requires sign-in.
                message = tail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
                print(f"::error title={name} failed::{message}")
            raise RuntimeError(f"{name} failed; see {output / (name + '.log')}")

    try:
        command("lint", [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"])
        for target in (
            "x86_64-unknown-linux-gnu",
            "x86_64-pc-windows-msvc",
            "aarch64-apple-darwin",
            "x86_64-apple-darwin",
        ):
            command(
                "dependencies-" + target,
                [
                    "uv",
                    "sync",
                    "--frozen",
                    "--dev",
                    "--all-extras",
                    "--dry-run",
                    "--offline",
                    "--no-build",
                    "--no-install-project",
                    "--python-platform",
                    target,
                ],
            )
        command(
            "tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "--test-evidence",
                str(output / "tests.json"),
            ],
        )
        record["capabilities"] = check_capabilities(
            json.loads((output / "tests.json").read_text(encoding="utf-8")),
            json.loads((ROOT / "scripts/capability_contracts.json").read_text(encoding="utf-8")),
        )
        (output / "capabilities.json").write_text(
            json.dumps(record["capabilities"], indent=2) + "\n", encoding="utf-8"
        )
        command("fixtures", ["uv", "run", "--no-sync", "ragvi", "verify"])
        command("build", ["uv", "build", "--out-dir", str(dist)])
        record["distributions"] = check_distributions(dist, tag)
        artifacts = distributions(dist, version)
        record["installations"] = []
        for artifact in artifacts:
            with tempfile.TemporaryDirectory(prefix="ragvi-release-") as temporary:
                record["installations"].append(
                    check_install(artifact, Path(temporary), offline=not online_install)
                )
        wheel = next(p for p in artifacts if p.suffix == ".whl")
        with tempfile.TemporaryDirectory(prefix="ragvi-extras-") as temporary:
            record["installations"].append(
                check_install(
                    wheel, Path(temporary), extras=["pdf", "semantic"], offline=not online_install
                )
            )
        record["status"] = "passed"
    except Exception as error:
        record["status"] = "failed"
        record["error"] = str(error)
        record["traceback"] = traceback.format_exc()
        raise
    finally:
        (output / "checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification/ci/local")
    parser.add_argument("--dist", type=Path, default=ROOT / "dist/release")
    parser.add_argument("--tag", default=os.environ.get("RAGVI_RELEASE_TAG") or None)
    parser.add_argument("--online-install", action="store_true")
    args = parser.parse_args()
    result = verify(
        args.output.resolve(), args.dist.resolve(), args.tag, online_install=args.online_install
    )
    print(f"PASS: {result['version']} on {result['platform']} {result['machine']}")
