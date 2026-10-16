"""Exercise an isolated upgrade from an actual, checksum-verified published wheel."""

import argparse
import json
import tempfile
from pathlib import Path

from scripts.check_portable_install import install_tool, run
from scripts.release_metadata import distributions, release_version, sha256

OLD_VERSION = "0.1.0"
OLD_SHA256 = "6dc10ba92245c332292f578591bbc88aab0d5827a1e445292c75fcc5dd5029ee"


def check(old: Path, candidate: Path, directory: Path, *, offline: bool = True) -> dict:
    if sha256(old) != OLD_SHA256:
        raise ValueError("Upgrade baseline must be the verified official 0.1.0 wheel")
    executable, client, env = install_tool(old, directory, offline=offline)
    legacy_version_output = run([executable, "--version"], cwd=client, env=env).strip()
    # The immutable 0.1.0 wheel prints a BM25S import notice on Windows.
    assert legacy_version_output.splitlines()[-1] == OLD_VERSION
    legacy = client / "legacy"
    run([executable, "tutorial", "--root", str(legacy)], cwd=client, env=env)
    original = {
        p.relative_to(legacy).as_posix(): sha256(p) for p in legacy.rglob("*") if p.is_file()
    }
    executable, client, env = install_tool(candidate, directory, reinstall=True, offline=offline)
    version = run([executable, "--version"], cwd=client, env=env).strip()
    assert version == release_version()
    workspace = legacy / "first-run"
    old_run = workspace / "runs/bm25-body.json"
    question = json.loads(old_run.read_text(encoding="utf-8"))["queries"][0]["question_id"]
    run([executable, "inspect", str(old_run), "--question", question], cwd=client, env=env)
    for format_name, extension in [("html", "html"), ("json", "json"), ("markdown", "md")]:
        run(
            [
                executable,
                "report",
                str(workspace / "evaluations/bm25-body.json"),
                str(client / ("legacy-export." + extension)),
                "--format",
                format_name,
            ],
            cwd=client,
            env=env,
        )
    assert original == {
        p.relative_to(legacy).as_posix(): sha256(p) for p in legacy.rglob("*") if p.is_file()
    }
    run([executable, "tutorial", "--root", str(client / "new-tutorial")], cwd=client, env=env)
    source = client / "data.txt"
    source.write_text("Reset requires eight seconds.", encoding="utf-8")
    run([executable, "bm25", str(source), "--query", "reset", "--no-input"], cwd=client, env=env)
    return {
        "status": "passed",
        "from_version": OLD_VERSION,
        "to_version": version,
        "old_sha256": OLD_SHA256,
        "candidate_sha256": sha256(candidate),
        "legacy_artifacts_unchanged": True,
        "legacy_version_stdout_notice": legacy_version_output != OLD_VERSION,
        "legacy_exports": ["html", "json", "markdown"],
        "limit": "Legacy reads retain legacy provenance; rerun experiments for modern validation.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    candidates = parser.add_mutually_exclusive_group(required=True)
    candidates.add_argument("--candidate", type=Path)
    candidates.add_argument("--candidate-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--online-install", action="store_true")
    args = parser.parse_args()
    candidate = args.candidate or next(
        p for p in distributions(args.candidate_dir, release_version()) if p.suffix == ".whl"
    )
    with tempfile.TemporaryDirectory(prefix="ragvi-upgrade-") as temporary:
        result = check(
            args.old.resolve(),
            candidate.resolve(),
            Path(temporary),
            offline=not args.online_install,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: upgrade, unchanged legacy artifacts, legacy exports and new portable commands")
