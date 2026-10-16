"""Install a wheel as a global-style tool and exercise it away from the checkout.

Uses only cached dependencies and isolated temporary tool/bin directories.
Run after `uv build`: uv run python scripts/check_portable_install.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def check_install(wheel: Path, directory: Path) -> None:
    client = directory / "customer folder"
    client.mkdir()
    tool_bin = directory / "bin"
    env = {
        **{key: value for key, value in os.environ.items() if not key.startswith("RAGVIDENCE_")},
        "UV_TOOL_DIR": str(directory / "tools"),
        "UV_TOOL_BIN_DIR": str(tool_bin),
        "PYTHONPATH": "",
        "PATH": str(tool_bin) + os.pathsep + os.environ.get("PATH", ""),
        "XDG_CONFIG_HOME": str(directory / "config"),
        "APPDATA": str(directory / "roaming"),
    }
    run(
        ["uv", "tool", "install", "--offline", "--python", sys.executable, str(wheel)],
        cwd=client,
        env=env,
    )
    executable = shutil.which("ragvi", path=env["PATH"])
    if not executable or Path(executable).parent != tool_bin:
        raise RuntimeError("The isolated global-style ragvi command was not installed")
    source = client / "manual α.md"
    text = "# Device\n\nHold the reset button for eight seconds.\n\nUse USB-C power.\n"
    source.write_text(text, encoding="utf-8")
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
    report = json.loads(reports[0].read_text())
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
    for technique, extra in [
        ("parent-child", []),
        ("heading-context", []),
        ("multi-query", ["--variants", str(variants)]),
        ("contextual", ["--prefixes", str(prefixes)]),
        ("import-data", ["--results", str(imported)]),
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
        evidence = json.loads(next(destination.glob("*/report.json")).read_text())
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
            "bm25,parent-child",
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
    comparison = json.loads(comparison_path.read_text())
    assert comparison["state"] == "complete" and comparison["baseline"] == "existing"
    assert len(comparison["participants"]) == 3
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
    mixed_data = json.loads(mixed_report.read_text())
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
    assert missing_extra.returncode != 0 and "ragvidence[pdf]" in missing_extra.stdout
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
        "source-only mode, HTML/JSON/JSONL/CSV, explicit configuration, missing PDF extra, "
        "reviewed spans, portable lexical modifiers, exact-context imports, comparisons/resume, "
        "unchanged input, verification and legacy tutorial"
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    wheels = sorted((root / "dist").glob("ragvidence-*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise SystemExit("Build the wheel first: uv build")
    with tempfile.TemporaryDirectory(prefix="ragvi-installed-") as temporary:
        check_install(wheels[-1], Path(temporary))
