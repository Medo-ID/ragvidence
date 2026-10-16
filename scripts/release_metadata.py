"""Shared release identities and exact distribution selection (standard library only)."""

import ast
import hashlib
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def project_metadata(root: Path = ROOT) -> dict:
    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def release_version(root: Path = ROOT) -> str:
    project = project_metadata(root)
    module = ast.parse((root / "src/ragvidence/__init__.py").read_text(encoding="utf-8"))
    runtime = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    )
    if project["version"] != runtime or not re.fullmatch(
        r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", runtime
    ):
        raise ValueError("Package and runtime versions must match a supported release version")
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    package = next(item for item in lock["package"] if item["name"] == project["name"])
    if package["version"] != runtime:
        raise ValueError("Lockfile version differs from the package; run uv lock")
    if project.get("license") != "Apache-2.0":
        raise ValueError("The free release must declare Apache-2.0")
    return runtime


def distributions(directory: Path, version: str) -> list[Path]:
    expected = {f"ragvidence-{version}-py3-none-any.whl", f"ragvidence-{version}.tar.gz"}
    actual = {p.name for p in directory.iterdir() if p.suffix in {".whl", ".gz"}}
    if actual != expected:
        raise ValueError(
            f"Expected exactly the release wheel and sdist: {sorted(expected)}; "
            f"found {sorted(actual)}"
        )
    return [directory / name for name in sorted(expected)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_identity(root: Path = ROOT) -> dict:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
    )
    return {"commit": commit, "working_tree_dirty": dirty}
