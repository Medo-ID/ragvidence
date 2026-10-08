"""Environment and bundled-asset health checks."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from raglab.data import load_dataset
from raglab.workspace import EXERCISE_ROOT


@dataclass(frozen=True)
class Check:
    status: str
    name: str
    detail: str


def run_health(workspace_root: Path) -> list[Check]:
    checks = [
        Check(
            "PASS" if sys.version_info[:2] == (3, 12) else "FAIL", "Python", sys.version.split()[0]
        )
    ]
    try:
        load_dataset(EXERCISE_ROOT)
        checks.append(Check("PASS", "Bundled exercise", "data and evidence references are valid"))
    except Exception as exc:
        checks.append(Check("FAIL", "Bundled exercise", str(exc)))
    required = ("bm25s", "jinja2", "numpy", "pydantic", "rich", "typer")
    missing = []
    versions = []
    for distribution in required:
        try:
            versions.append(f"{distribution}={importlib.metadata.version(distribution)}")
        except importlib.metadata.PackageNotFoundError:
            missing.append(distribution)
    checks.append(
        Check(
            "FAIL" if missing else "PASS",
            "Dependencies",
            f"missing: {', '.join(missing)}" if missing else ", ".join(versions),
        )
    )
    try:
        workspace_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=workspace_root):
            pass
        checks.append(Check("PASS", "Workspace", f"writable: {workspace_root}"))
    except OSError as exc:
        checks.append(Check("FAIL", "Workspace", str(exc)))
    semantic = importlib.util.find_spec("fastembed") is not None
    checks.append(
        Check(
            "PASS" if semantic else "WARN",
            "Semantic extra",
            "available" if semantic else "not installed; see docs/user-guide.md",
        )
    )
    checks.append(
        Check("PASS", "Privacy", "no account, telemetry, or API key required for local BM25")
    )
    return checks
