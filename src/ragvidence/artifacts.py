"""Canonical identities and atomic, non-overwriting artifact storage."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

HASH_ALGORITHM = "canonical-json-v1"


def _canonical(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _canonical(value.model_dump(mode="python"))
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("Artifact object keys must be strings")
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, set | frozenset):
        return sorted(
            (_canonical(item) for item in value),
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False, allow_nan=False),
        )
    if isinstance(value, list | tuple):
        return [_canonical(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    """Sort unordered values, while retaining meaningful list/ranking order."""
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def json_value(value: Any) -> Any:
    """Preserve set semantics until conversion to a deterministic JSON value."""
    return _canonical(value)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def write_bytes(output: Path, content: bytes) -> None:
    """Publish a complete file atomically, without replacing an existing file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".ragvi-", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError as exc:
            raise FileExistsError(f"Refusing to overwrite existing artifact: {output}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def write_text(output: Path, content: str) -> None:
    write_bytes(output, content.encode("utf-8"))


def write_json(output: Path, value: Any) -> None:
    write_text(
        output, json.dumps(_canonical(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
