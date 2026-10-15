import json
from copy import deepcopy

import pytest

from ragvidence.artifacts import canonical_bytes, content_hash, write_json, write_text
from ragvidence.comparison import compare_evaluations
from ragvidence.data import load_dataset
from ragvidence.evaluation.evaluator import evaluate_run
from ragvidence.models import StrategyConfig
from ragvidence.reporting.payload import build_report
from ragvidence.runner import run_experiment
from ragvidence.workspace import EXERCISE_ROOT


def test_canonical_serialization_sorts_sets_but_preserves_rankings():
    assert canonical_bytes({"tags": {"z", "a"}}) == b'{"tags":["a","z"]}'
    assert content_hash(["a", "b"]) != content_hash(["b", "a"])
    assert content_hash({"b": 1, "a": 2}) == content_hash({"a": 2, "b": 1})
    with pytest.raises(ValueError):
        canonical_bytes({"score": float("nan")})


def test_artifact_publish_does_not_overwrite_and_cleans_temporary_files(tmp_path):
    target = tmp_path / "result.json"
    write_json(target, {"tags": {"B", "A"}})
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        write_text(target, "replacement")
    assert target.read_bytes() == original
    assert json.loads(original) == {"tags": ["A", "B"]}
    assert list(tmp_path.iterdir()) == [target]


def evaluated_fixture():
    sources, questions = load_dataset(EXERCISE_ROOT)
    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="validation", strategy="bm25"))
    return evaluate_run(run, questions, sources=sources)


def test_modern_evaluation_tampering_is_rejected_before_comparison_or_export():
    valid = evaluated_fixture()
    forged = deepcopy(valid)
    forged["summary"]["successful"] += 1
    with pytest.raises(ValueError, match="differs"):
        compare_evaluations(valid, forged)
    with pytest.raises(ValueError, match="differs"):
        build_report(forged)


def test_shareable_report_excludes_internal_source_snapshot():
    evaluated = evaluated_fixture()
    report = build_report(evaluated)
    assert "_validation" not in report["baseline"]
    assert "_validation" in evaluated


def test_legacy_duplicate_evaluation_records_are_not_silently_collapsed():
    legacy = {"questions": [{"question_id": "Q"}, {"question_id": "Q"}]}
    with pytest.raises(ValueError, match="duplicate"):
        compare_evaluations(legacy, legacy)
