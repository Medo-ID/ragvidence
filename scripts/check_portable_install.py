"""Install a wheel as a global-style tool and exercise it away from the checkout.

Uses locked dependencies and isolated temporary tool/bin directories. Offline by
default; --online-install allows package-index metadata/downloads on fresh runners.
Run after `uv build`: uv run python scripts/check_portable_install.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def install_tool(
    wheel: Path,
    directory: Path,
    *,
    extras: list[str] | None = None,
    reinstall: bool = False,
    offline: bool = True,
) -> tuple[str, Path, dict[str, str]]:
    extras = extras or []
    client = directory / "customer folder"
    client.mkdir(exist_ok=True)
    tool_bin = directory / "bin"
    env = {
        **{key: value for key, value in os.environ.items() if not key.startswith("RAGVIDENCE_")},
        "UV_TOOL_DIR": str(directory / "tools"),
        "UV_TOOL_BIN_DIR": str(tool_bin),
        "PYTHONPATH": "",
        "PYTHONUTF8": "1",
        "HF_HUB_OFFLINE": "1",
        "PATH": str(tool_bin) + os.pathsep + os.environ.get("PATH", ""),
        "XDG_CONFIG_HOME": str(directory / "config"),
        "APPDATA": str(directory / "roaming"),
    }
    target = (
        f"ragvidence[{','.join(extras)}] @ {wheel.resolve().as_uri()}"
        if extras
        else str(wheel.resolve())
    )
    constraints = directory / "locked-requirements.txt"
    run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--all-extras",
            "--no-emit-project",
            "--no-hashes",
            "--output-file",
            str(constraints),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
    )
    run(
        [
            "uv",
            "tool",
            "install",
            *(["--offline"] if offline else []),
            "--constraint",
            str(constraints),
            "--python",
            sys.executable,
            *(["--reinstall"] if reinstall else []),
            target,
        ],
        cwd=client,
        env=env,
    )
    executable = shutil.which("ragvi", path=env["PATH"])
    if not executable or Path(executable).parent != tool_bin:
        raise RuntimeError("The isolated global-style ragvi command was not installed")
    return executable, client, env


def check_install(
    wheel: Path, directory: Path, *, extras: list[str] | None = None, offline: bool = True
) -> dict:
    extras = extras or []
    executable, client, env = install_tool(wheel, directory, extras=extras, offline=offline)
    expected_version = wheel.name.removeprefix("ragvidence-").split("-")[0].removesuffix(".tar.gz")
    assert run([executable, "--version"], cwd=client, env=env).strip() == expected_version
    assert "all included features" in run([executable, "edition"], cwd=client, env=env)
    source = client / "manual α.md"
    text = "# Device\n\nHold the reset button for eight seconds.\n\nUse USB-C power.\n"
    source.write_bytes(text.encode("utf-8"))
    output = run(
        [
            executable,
            "bm25",
            source.name,
            "--query",
            "reset button",
            "--format",
            "html",
            "--format",
            "json",
            "--format",
            "markdown",
            "--no-input",
        ],
        cwd=client,
        env=env,
    )
    reports = list((client / "ragvi-reports").glob("*/report.json"))
    if len(reports) != 1:
        raise RuntimeError("Expected one automatically generated report directory")
    root = reports[0].parent
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["evaluation_level"] == "retrieval_inspection"
    assert "eight seconds" in report["questions"][0]["hits"][0]["text"]
    assert (root / "report.html").is_file() and (root / "report.md").is_file()
    assert source.read_text(encoding="utf-8") == text
    capabilities = json.loads(
        run([executable, "techniques", "--format", "json"], cwd=client, env=env)
    )
    assert {item["name"] for item in capabilities} >= {
        "semantic",
        "hybrid",
        "parent-child",
        "import-data",
        "metadata-filter",
        "mmr",
        "rewrite",
        "auto-multi-query",
        "compress",
    }
    original = report["input"]["sources"][0]
    references = client / "reviewed.json"
    start = text.index("eight seconds")
    references.write_text(
        json.dumps(
            {
                "corpus_hash": report["input"]["corpus_hash"],
                "evidence": [
                    {
                        "evidence_id": "RESET",
                        "spans": [
                            {
                                "source_id": original["source_unit_id"],
                                "start": start,
                                "end": start + 13,
                                "text": "eight seconds",
                            }
                        ],
                    }
                ],
                "questions": [
                    {
                        "question_id": "Q",
                        "question": "reset",
                        "split": "dev",
                        "answerable": True,
                        "required_evidence_ids": ["RESET"],
                    }
                ],
            }
        )
    )
    variants = client / "variants.json"
    variants.write_text('{"Q":["reset button"]}')
    prefixes = client / "prefixes.json"
    prefixes.write_text(
        json.dumps(
            {
                original["source_unit_id"]: {
                    "text_hash": original["text_hash"],
                    "prefix": "Device reset instructions",
                }
            }
        )
    )
    imported = client / "results.jsonl"
    imported.write_text(
        json.dumps(
            {
                "question_id": "Q",
                "hits": [
                    {
                        "source_id": original["source_unit_id"],
                        "start": 0,
                        "end": len(text),
                        "text": text,
                    }
                ],
            }
        )
    )
    filters = client / "filters.json"
    filters.write_text('{"all":[{"field":"format","op":"eq","value":".md"}]}')
    for technique, extra in [
        ("parent-child", []),
        ("heading-context", []),
        ("multi-query", ["--variants", str(variants)]),
        ("contextual", ["--prefixes", str(prefixes)]),
        ("import-data", ["--results", str(imported)]),
        ("metadata-filter", ["--filters", str(filters)]),
        ("compress", []),
    ]:
        destination = client / technique
        run(
            [
                executable,
                technique,
                str(source),
                "--reviewed",
                str(references),
                "--format",
                "json",
                "--output",
                str(destination),
                "--no-input",
                *extra,
            ],
            cwd=client,
            env=env,
        )
        evidence = json.loads(next(destination.glob("*/report.json")).read_text(encoding="utf-8"))
        assert evidence["questions"][0]["metrics"]["sufficient_evidence"] is True
        assert evidence["questions"][0]["stages"]
    comparison_root = client / "comparisons"
    comparison_output = run(
        [
            executable,
            "compare-data",
            str(source),
            "--reviewed",
            str(references),
            "--results",
            str(imported),
            "--techniques",
            "bm25,parent-child,metadata-filter,compress",
            "--filters",
            str(filters),
            "--format",
            "json",
            "--format",
            "html",
            "--format",
            "markdown",
            "--output",
            str(comparison_root),
            "--no-input",
        ],
        cwd=client,
        env=env,
    )
    comparison_path = next(comparison_root.glob("*/exports/*/report.json"))
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    assert comparison["state"] == "complete" and comparison["baseline"] == "existing"
    assert len(comparison["participants"]) == 5
    assert comparison["participants"][0]["resources"]["query_ms"]["mean_known"] is None
    assert "HTML report:" in comparison_output
    comparison_directory = comparison_path.parents[2]
    run(
        [
            executable,
            "compare-data",
            "unused-frozen-input",
            "--resume",
            str(comparison_directory),
            "--format",
            "json",
            "--no-input",
        ],
        cwd=client,
        env=env,
    )
    # Exercise all dependency-free structured loaders from the installed wheel.
    mixed = client / "mixed data"
    mixed.mkdir()
    (mixed / "manual.html").write_text("<h1>Reset</h1><p>Hold for eight seconds.</p>")
    (mixed / "documents.json").write_text('[{"text":"Reset for eight seconds."}]')
    (mixed / "records.jsonl").write_text('{"body":"Reset for eight seconds."}\n')
    (mixed / "rows.csv").write_text("id,content\nreset,Reset for eight seconds.\n")
    options = client / "portable.toml"
    options.write_text('k = 1\nformats = ["json"]\noutput = "mixed-results"\n')
    run(
        [
            executable,
            "bm25",
            str(mixed),
            "--query",
            "reset",
            "--config",
            str(options),
            "--no-input",
        ],
        cwd=client,
        env=env,
    )
    mixed_report = next((client / "mixed-results").glob("*/report.json"))
    mixed_data = json.loads(mixed_report.read_text(encoding="utf-8"))
    assert mixed_data["input"]["file_count"] == 4
    assert mixed_data["manifest"]["config"]["k"] == 1
    assert mixed_data["questions"][0]["hits"][0]["location"]
    pdf = client / "optional.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    missing_extra = subprocess.run(
        [executable, "bm25", str(pdf), "--no-input"],
        cwd=client,
        env=env,
        capture_output=True,
        text=True,
    )
    if "pdf" in extras:
        fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/portable/text-pages.pdf"
        shutil.copyfile(fixture, pdf)
        run(
            [
                executable,
                "bm25",
                str(pdf),
                "--query",
                "reset",
                "--format",
                "json",
                "--output",
                str(client / "pdf-results"),
                "--no-input",
            ],
            cwd=client,
            env=env,
        )
        pdf_report = json.loads(
            next((client / "pdf-results").glob("*/report.json")).read_text(encoding="utf-8")
        )
        assert pdf_report["input"]["document_count"] == 2
    else:
        assert missing_extra.returncode != 0 and "ragvidence[pdf]" in missing_extra.stdout
    # Read-only inputs must remain byte-identical and work with a separate output root.
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        source.chmod(0o444)
        run(
            [
                executable,
                "bm25",
                str(source),
                "--query",
                "reset",
                "--format",
                "json",
                "--output",
                str(client / "read-only-results"),
                "--no-input",
            ],
            cwd=client,
            env=env,
        )
    finally:
        source.chmod(0o644)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest

    run(
        [executable, "bm25", str(source), "--no-input", "--output", str(client / "source-only")],
        cwd=client,
        env=env,
    )
    run([executable, "verify"], cwd=client, env=env)
    run([executable, "tutorial", "--root", str(client / "tutorial")], cwd=client, env=env)
    print(output.strip())
    print(
        "PASS: installed command, unrelated directory, Unicode/space paths, all exports, "
        "source-only mode, HTML/JSON/JSONL/CSV, explicit configuration, PDF extra contract, "
        "reviewed spans, portable lexical modifiers, exact-context imports, comparisons/resume, "
        "unchanged input, verification and legacy tutorial"
    )

    return {
        "status": "passed",
        "platform": platform.system(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "version": expected_version,
        "distribution": wheel.name,
        "extras": extras,
        "installation_network": "offline" if offline else "package-index only; models offline",
        "dependency_policy": "uv.lock constraints",
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "journeys": [
            "global-style command",
            "unrelated directory",
            "Unicode and space paths",
            "source-only",
            "questions",
            "reviewed spans",
            "all exports",
            "structured loaders",
            "filters",
            "compression",
            "comparison",
            "resume",
            "read-only input",
            "legacy tutorial",
            "installed verification",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", type=Path)
    parser.add_argument("--extras", default="", help="pdf,semantic or empty for core")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--online-install", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    wheels = sorted((root / "dist").glob("**/ragvidence-*.whl"), key=lambda p: p.stat().st_mtime)
    artifact = args.distribution or (wheels[-1] if wheels else None)
    if artifact is None:
        raise SystemExit("Build the wheel first: uv build --out-dir dist/release")
    with tempfile.TemporaryDirectory(prefix="ragvi-installed-") as temporary:
        result = check_install(
            artifact.resolve(),
            Path(temporary),
            extras=[v for v in args.extras.split(",") if v],
            offline=not args.online_install,
        )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
