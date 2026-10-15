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
        **os.environ,
        "UV_TOOL_DIR": str(directory / "tools"),
        "UV_TOOL_BIN_DIR": str(tool_bin),
        "PYTHONPATH": "",
        "PATH": str(tool_bin) + os.pathsep + os.environ.get("PATH", ""),
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
        "source-only mode, unchanged input, verification and legacy tutorial"
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    wheels = sorted((root / "dist").glob("ragvidence-*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise SystemExit("Build the wheel first: uv build")
    with tempfile.TemporaryDirectory(prefix="ragvi-installed-") as temporary:
        check_install(wheels[-1], Path(temporary))
