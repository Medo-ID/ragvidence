"""Question acquisition without inventing evaluation labels."""

import json
from pathlib import Path

from ragvidence.artifacts import content_hash
from ragvidence.models import SearchQuestion


def load_questions(queries: list[str], question_file: Path | None) -> list[SearchQuestion]:
    questions = [
        SearchQuestion(question_id=f"query-{index}", question=text)
        for index, text in enumerate(queries, start=1)
    ]
    if question_file is not None:
        if question_file.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Question file exceeds 5 MiB")
        raw = question_file.read_text(encoding="utf-8-sig")
        if question_file.suffix.lower() == ".jsonl":
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        elif question_file.suffix.lower() == ".json":
            records = json.loads(raw)
            if not isinstance(records, list):
                raise ValueError("Question JSON must be an array of question objects")
        elif question_file.suffix.lower() == ".txt":
            records = [line.strip() for line in raw.splitlines() if line.strip()]
        else:
            raise ValueError("Use TXT, JSON or JSONL for questions")
        if not records:
            raise ValueError("Question file must contain at least one question")
        for index, record in enumerate(records, start=1):
            if isinstance(record, str):
                record = {"question": record}
            if not isinstance(record, dict):
                raise ValueError(f"Question {index} must be text or an object")
            if set(record) - {"question_id", "question"}:
                raise ValueError(
                    "Portable question files currently accept question_id and question only. "
                    "Use the workspace evaluation commands for reviewed evidence labels."
                )
            text = record.get("question")
            questions.append(
                SearchQuestion(
                    question_id=record.get(
                        "question_id",
                        "file-" + content_hash({"index": index, "question": text})[:12],
                    ),
                    question=text,
                )
            )
    identifiers = [question.question_id for question in questions]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Question IDs must be unique across flags and the question file")
    return questions
