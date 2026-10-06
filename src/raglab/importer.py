"""Import ranked results from an external retrieval pipeline."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from raglab import __version__
from raglab.data import DatasetError, canonical_dataset_bytes, load_dataset
from raglab.models import ExperimentRun, QueryRun, RetrievalHit, RunManifest, StrategyConfig


def import_retrieval_run(
    workspace: Path,
    input_path: Path,
    *,
    name: str,
    k: int,
) -> ExperimentRun:
    """Validate, enrich and normalize an external JSONL ranking."""
    sources, questions = load_dataset(workspace)
    source_by_id = {source.source_unit_id: source for source in sources}
    question_ids = {question.question_id for question in questions}
    raw_records = _read_jsonl(input_path)

    seen: set[str] = set()
    queries: list[QueryRun] = []
    for line_number, record in raw_records:
        question_id = record.get("question_id")
        if not isinstance(question_id, str) or not question_id:
            raise DatasetError(f"{input_path}:{line_number}: question_id must be a string")
        if question_id not in question_ids:
            raise DatasetError(f"{input_path}:{line_number}: unknown question_id {question_id!r}")
        if question_id in seen:
            raise DatasetError(f"{input_path}:{line_number}: duplicate question_id {question_id!r}")
        seen.add(question_id)
        hits = _parse_hits(input_path, line_number, record.get("hits"), source_by_id, k)
        queries.append(QueryRun(question_id=question_id, hits=hits, query_time_ms=0.0))

    missing = question_ids - seen
    if missing:
        raise DatasetError(f"Imported run is missing question IDs: {sorted(missing)}")

    config = StrategyConfig(name=name, strategy="imported", representation="body", k=k)
    dataset_hash = hashlib.sha256(canonical_dataset_bytes(sources, questions)).hexdigest()
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_key = f"{name}:{dataset_hash}:{timestamp}".encode()
    return ExperimentRun(
        manifest=RunManifest(
            run_id=hashlib.sha256(run_key).hexdigest()[:12],
            created_at=timestamp,
            product_version=__version__,
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            dataset_hash=dataset_hash,
            config=config,
            index_time_ms=0.0,
            warnings=["Timing is unavailable for imported retrieval results."],
        ),
        queries=queries,
    )


def _read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DatasetError(f"Cannot read {path}: {exc}") from exc
    records = []
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DatasetError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise DatasetError(f"{path}:{line_number}: expected a JSON object")
        records.append((line_number, value))
    if not records:
        raise DatasetError(f"{path}: expected at least one record")
    return records


def _parse_hits(
    path: Path,
    line_number: int,
    value: Any,
    source_by_id: dict[str, Any],
    k: int,
) -> list[RetrievalHit]:
    if not isinstance(value, list):
        raise DatasetError(f"{path}:{line_number}: hits must be a list")
    hits = []
    seen_sources: set[str] = set()
    for expected_rank, raw_hit in enumerate(value[:k], start=1):
        if not isinstance(raw_hit, dict):
            raise DatasetError(f"{path}:{line_number}: hit {expected_rank} must be an object")
        source_id = raw_hit.get("source_unit_id")
        if source_id not in source_by_id:
            raise DatasetError(
                f"{path}:{line_number}: hit {expected_rank} references unknown source {source_id!r}"
            )
        if source_id in seen_sources:
            raise DatasetError(f"{path}:{line_number}: duplicate source {source_id!r}")
        seen_sources.add(source_id)
        supplied_rank = raw_hit.get("rank", expected_rank)
        if supplied_rank != expected_rank:
            raise DatasetError(
                f"{path}:{line_number}: expected contiguous rank {expected_rank}, "
                f"got {supplied_rank!r}"
            )
        score = raw_hit.get("score", 0.0)
        if not isinstance(score, int | float) or isinstance(score, bool):
            raise DatasetError(f"{path}:{line_number}: hit {expected_rank} score must be numeric")
        source = source_by_id[source_id]
        hits.append(
            RetrievalHit(
                source_unit_id=source_id,
                rank=expected_rank,
                score=float(score),
                evidence_ids=source.evidence_ids,
                preview=source.body[:240],
                metadata={"document_id": source.document_id, "imported": True},
            )
        )
    return hits
