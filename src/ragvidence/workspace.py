"""Managed workspace creation and recoverable restore."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent
EXERCISE_ROOT = PACKAGE_ROOT / "exercises" / "heading_context"


def create_workspace(root: Path, name: str) -> Path:
    target = (root / name).resolve()
    managed = root.resolve()
    if managed not in target.parents or target == managed:
        raise ValueError("Workspace must be a named child of the managed root")
    if target.exists():
        raise FileExistsError(f"Workspace already exists: {target}")
    shutil.copytree(EXERCISE_ROOT, target)
    return target


def restore_workspace(root: Path, name: str) -> tuple[Path, Path]:
    target = (root / name).resolve()
    managed = root.resolve()
    if managed not in target.parents or not target.is_dir():
        raise ValueError("Can only restore an existing managed workspace")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup = target.with_name(f"{target.name}.backup-{stamp}")
    target.rename(backup)
    shutil.copytree(EXERCISE_ROOT, target)
    return target, backup
