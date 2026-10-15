"""Regression cases for reproducible and trustworthy retrieval artifacts."""

import json
import os
import subprocess
import sys

import pytest
from pydantic import ValidationError

from ragvidence.data import load_dataset
from ragvidence.evaluation.evaluator import evaluate_run
from ragvidence.importer import import_retrieval_run
from ragvidence.models import RetrievalHit, StrategyConfig
from ragvidence.runner import run_experiment
from ragvidence.workspace import EXERCISE_ROOT


def test_dataset_digest_is_stable_across_hash_seeds():
    code = (
        "import hashlib; from ragvidence.data import load_dataset, canonical_dataset_bytes; "
        "from ragvidence.workspace import EXERCISE_ROOT; "
        "print(hashlib.sha256(canonical_dataset_bytes(*load_dataset(EXERCISE_ROOT))).hexdigest())"
    )
    digests = [
        subprocess.check_output(
            [sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": str(seed)}, text=True
        ).strip()
        for seed in (1, 2, 3)
    ]
    assert len(set(digests)) == 1


def test_evaluation_artifact_validates_in_another_process_hash_seed(tmp_path):
    from ragvidence.artifacts import write_json

    sources, questions = load_dataset(EXERCISE_ROOT)
    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="cross-process", strategy="bm25"))
    artifact = tmp_path / "evaluation.json"
    write_json(artifact, evaluate_run(run, questions, sources=sources))
    code = (
        "import json,sys; from pathlib import Path; "
        "from ragvidence.evaluation.validation import validate_evaluation; "
        "validate_evaluation(json.loads(Path(sys.argv[1]).read_text())); print('VALID')"
    )
    for seed in (1, 2, 3):
        result = subprocess.run(
            [sys.executable, "-c", code, str(artifact)],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "VALID" in result.stdout


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -float("inf")])
def test_hit_scores_must_be_finite(score):
    with pytest.raises(ValidationError):
        RetrievalHit(source_unit_id="S", rank=1, score=score)


@pytest.mark.parametrize(
    "mutation",
    ["dataset", "evidence", "source", "missing", "duplicate", "rank", "depth", "context"],
)
def test_evaluation_rejects_inconsistent_run(mutation):
    sources, questions = load_dataset(EXERCISE_ROOT)
    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="integrity", strategy="bm25"))
    if mutation == "dataset":
        sources[0].body += " changed"
    elif mutation == "evidence":
        run.queries[0].hits[0].evidence_ids = {"FORGED"}
    elif mutation == "source":
        run.queries[0].hits[0].source_unit_id = "UNKNOWN"
    elif mutation == "missing":
        run.queries.pop()
    elif mutation == "duplicate":
        run.queries.append(run.queries[0])
    elif mutation == "rank":
        run.queries[0].hits[0].rank = 3
    elif mutation == "context":
        run.queries[0].rendered_context = "FORGED CONTEXT"
    else:
        run.queries[0].hits.append(run.queries[0].hits[0])
    with pytest.raises(ValueError):
        evaluate_run(run, questions, sources=sources)


def test_import_validates_results_beyond_the_selected_depth(tmp_path):
    _, questions = load_dataset(EXERCISE_ROOT)
    path = tmp_path / "external.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                {
                    "question_id": question.question_id,
                    "hits": [
                        {"source_unit_id": "SEC-ORION-42-RESET", "rank": 1},
                        {"source_unit_id": "DOES-NOT-EXIST", "rank": 2},
                    ],
                }
            )
            for question in questions
        )
    )
    with pytest.raises(ValueError, match="unknown source"):
        import_retrieval_run(EXERCISE_ROOT, path, name="external", k=1)
