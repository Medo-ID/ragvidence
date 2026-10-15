"""JSONL loading and cross-record integrity validation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ValidationError

from ragvidence.artifacts import canonical_bytes
from ragvidence.models import QuestionCase, SearchQuestion, SourceUnit


class DatasetError(ValueError):
    """A dataset cannot be evaluated safely."""


def load_jsonl[ModelT: BaseModel](path: Path, model: type[ModelT]) -> list[ModelT]:
    records: list[ModelT] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise DatasetError(f"Cannot read {path}: {exc}") from exc
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            records.append(model.model_validate_json(raw))
        except (ValidationError, ValueError) as exc:
            raise DatasetError(f"{path}:{line_number}: {exc}") from exc
    if not records:
        raise DatasetError(f"{path}: expected at least one record")
    return records


def load_dataset(root: Path) -> tuple[list[SourceUnit], list[QuestionCase]]:
    sources = load_jsonl(root / "sources.jsonl", SourceUnit)
    questions = load_jsonl(root / "questions.jsonl", QuestionCase)
    validate_dataset(sources, questions)
    return sources, questions


def validate_search_inputs(sources: list[SourceUnit], questions: list[SearchQuestion]) -> None:
    if not sources:
        raise DatasetError("Expected at least one source unit")
    source_ids = [item.source_unit_id for item in sources]
    question_ids = [item.question_id for item in questions]
    duplicate_sources = _duplicates(source_ids)
    duplicate_questions = _duplicates(question_ids)
    if duplicate_sources:
        raise DatasetError(f"Duplicate source_unit_id values: {sorted(duplicate_sources)}")
    if duplicate_questions:
        raise DatasetError(f"Duplicate question_id values: {sorted(duplicate_questions)}")


def validate_dataset(sources: list[SourceUnit], questions: list[QuestionCase]) -> None:
    validate_search_inputs(sources, questions)
    evidence = {evidence_id for source in sources for evidence_id in source.evidence_ids}
    missing = {
        evidence_id
        for question in questions
        for evidence_id in question.required_evidence_ids
        if evidence_id not in evidence
    }
    if missing:
        raise DatasetError(f"Questions reference unknown evidence IDs: {sorted(missing)}")


def canonical_dataset_bytes(
    sources: list[SourceUnit], questions: list[QuestionCase] | list[SearchQuestion]
) -> bytes:
    return canonical_bytes({"sources": sources, "questions": questions})


def _duplicates(values: list[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if count > 1}
