"""Application service for ordinary-file retrieval and automatic report export."""

from __future__ import annotations

import os
import re
import sys
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ragvidence.artifacts import content_hash, write_json, write_text
from ragvidence.config import Settings
from ragvidence.ingestion import load_corpus
from ragvidence.models import SearchQuestion, StrategyConfig
from ragvidence.reporting.inspection import build_inspection_report
from ragvidence.reporting.render import render_report
from ragvidence.runner import execute_retrieval, write_run

EXPORT_EXTENSIONS = {"html": "html", "json": "json", "markdown": "md"}


@dataclass(frozen=True)
class PortableResult:
    directory: Path
    report: dict[str, Any]
    exports: dict[str, Path]


def normalize_formats(formats: list[str] | None) -> list[str]:
    selected = list(dict.fromkeys(formats or ["html"]))
    if any(value not in EXPORT_EXTENSIONS for value in selected):
        raise ValueError("Supported report formats: html, json, markdown")
    return selected


def default_cache_dir() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Caches"
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "ragvidence"


def _create_output_directory(root: Path, input_name: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "-", input_name).strip("-")[:60] or "data"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    directory = root / f"{safe_name}-{stamp}-{uuid4().hex[:12]}"
    directory.mkdir(mode=0o700)
    write_json(directory / ".ragvi-run.json", {"schema_version": 1, "kind": "ragvi-run"})
    return directory


def run_portable(
    source: Path,
    questions: list[SearchQuestion],
    config: StrategyConfig,
    *,
    output_root: Path,
    formats: list[str] | None = None,
    question_file: Path | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    cache_dir: Path | None = None,
) -> PortableResult:
    selected_formats = normalize_formats(formats)
    exclude = [output_root, *([question_file] if question_file else [])]
    snapshot = load_corpus(source, exclude=exclude, size=chunk_size, overlap=chunk_overlap)
    name = source.resolve().name
    directory = _create_output_directory(output_root, source.resolve().stem)
    try:
        write_json(directory / "snapshot.json", snapshot)
        write_json(directory / "questions.json", questions)
        # The portable path deliberately ignores any .env in the data directory.
        settings = Settings(_env_file=None)
        identity = content_hash({"sources": snapshot.passages, "questions": questions})
        level = "retrieval_inspection" if questions else "ingestion_only"
        run = execute_retrieval(
            snapshot.passages,
            questions,
            config,
            cache_dir=cache_dir or default_cache_dir(),
            settings=settings,
            dataset_hash=identity,
            evaluation_level=level,
            corpus_hash=snapshot.corpus_hash,
            input_preparation=snapshot.preparation,
        )
        write_run(run, directory / "run.json")
        report = build_inspection_report(snapshot, questions, run, name=name)
        exports = {}
        for format in selected_formats:
            target = directory / f"report.{EXPORT_EXTENSIONS[format]}"
            write_text(target, render_report(report, format))
            exports[format] = target
        write_json(
            directory / "status.json",
            {"state": "complete", "run_id": run.manifest.run_id, "evaluation_level": level},
        )
    except Exception as exc:
        with suppress(OSError):
            write_json(directory / "status.json", {"state": "failed", "error": str(exc)})
        raise RuntimeError(f"Run failed; artifacts in {directory}: {exc}") from exc
    return PortableResult(directory, report, exports)
