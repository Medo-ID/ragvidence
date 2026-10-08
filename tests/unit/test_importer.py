import json
from pathlib import Path

import pytest

from ragvidence.data import DatasetError, load_dataset
from ragvidence.importer import import_retrieval_run
from ragvidence.workspace import EXERCISE_ROOT


def _write_complete_import(path: Path, *, bad_source: bool = False) -> None:
    _, questions = load_dataset(EXERCISE_ROOT)
    lines = []
    for question in questions:
        source_id = "MISSING" if bad_source and not lines else "SEC-ORION-42-RESET"
        lines.append(
            json.dumps(
                {
                    "question_id": question.question_id,
                    "hits": [{"source_unit_id": source_id, "rank": 1, "score": 0.75}],
                }
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_import_enriches_hits_with_reviewed_evidence(tmp_path: Path) -> None:
    input_path = tmp_path / "external.jsonl"
    _write_complete_import(input_path)
    run = import_retrieval_run(EXERCISE_ROOT, input_path, name="external", k=1)
    assert run.manifest.config.strategy == "imported"
    assert run.queries[0].hits[0].evidence_ids == {"E-ORION-42-RESET"}
    assert len(run.queries) == 12


def test_import_rejects_unknown_source(tmp_path: Path) -> None:
    input_path = tmp_path / "external.jsonl"
    _write_complete_import(input_path, bad_source=True)
    with pytest.raises(DatasetError, match="unknown source"):
        import_retrieval_run(EXERCISE_ROOT, input_path, name="external", k=1)


def test_import_requires_all_questions(tmp_path: Path) -> None:
    input_path = tmp_path / "external.jsonl"
    input_path.write_text('{"question_id":"DEV-01","hits":[]}\n')
    with pytest.raises(DatasetError, match="missing question IDs"):
        import_retrieval_run(EXERCISE_ROOT, input_path, name="external", k=1)
