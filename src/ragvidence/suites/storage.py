"""Immutable suite inputs, safe members and validated per-attempt checkpoints."""

import hashlib
import json
from pathlib import Path

from ragvidence.artifacts import write_bytes, write_json


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def member(root: Path, relative: str) -> Path:
    path = root / relative
    if (
        Path(relative).is_absolute()
        or path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError("Suite artifact path escapes the comparison directory")
    return path


def read_json(path: Path):
    if path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError("Suite artifact exceeds 512 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def freeze_file(root: Path, source: Path, *, max_bytes: int = 50 * 1024 * 1024) -> str:
    if source.stat().st_size > max_bytes:
        raise ValueError("Suite sidecar exceeds its file limit")
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    relative = f"inputs/{digest}{source.suffix.lower()}"
    target = member(root, relative)
    if not target.exists():
        write_bytes(target, raw)
    elif file_digest(target) != digest:
        raise ValueError("Frozen input digest mismatch")
    return relative


def seal_attempt(directory: Path) -> None:
    names = ["run.json", "search-sources.json", "report.json", "status.json"]
    if (directory / "evaluation.json").exists():
        names.append("evaluation.json")
    write_json(
        directory / "checkpoint.json", {name: file_digest(directory / name) for name in names}
    )


def verify_checkpoint(directory: Path) -> None:
    values = read_json(directory / "checkpoint.json")
    if (
        not isinstance(values, dict)
        or not {"run.json", "search-sources.json", "report.json", "status.json"} <= values.keys()
    ):
        raise ValueError("Incomplete comparison checkpoint")
    for name, digest in values.items():
        if file_digest(member(directory, name)) != digest:
            raise ValueError(f"Comparison checkpoint mismatch: {name}")
