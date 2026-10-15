"""Verify modern evaluation artifacts from their original snapshot and run."""

from typing import Any

from ragvidence.artifacts import canonical_bytes
from ragvidence.models import ExperimentRun, QuestionCase, SourceUnit


def validate_evaluation(value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError("Evaluation must be an object")
    try:
        identifiers = [question["question_id"] for question in value["questions"]]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Evaluation contains duplicate question IDs")
        config = value["manifest"]["config"]
        if not isinstance(value["manifest"]["dataset_hash"], str):
            raise ValueError("Evaluation requires a dataset hash")
        if type(config["k"]) is not int or config["k"] < 1:
            raise ValueError("Evaluation retrieval depth must be a positive integer")
        for question in value["questions"]:
            status = question["sufficient_evidence"]
            if status is not None and not isinstance(status, bool):
                raise ValueError("Evidence sufficiency must be boolean or null")
        version = value.get("schema_version", 1)
        if type(version) is not int or version not in {1, 2}:
            raise ValueError("Unsupported evaluation schema version")
        if version == 1:
            return  # Explicit legacy read; no new provenance claim.
        from ragvidence.evaluation.evaluator import evaluate_run

        proof = value["_validation"]
        sources = [SourceUnit.model_validate(item) for item in proof["sources"]]
        questions = [QuestionCase.model_validate(item) for item in proof["questions"]]
        run = ExperimentRun.model_validate(proof["run"])
        expected = evaluate_run(run, questions, sources=sources)
        if canonical_bytes(value) != canonical_bytes(expected):
            raise ValueError("Evaluation differs from the validated run; evaluate it again")
    except (KeyError, TypeError) as exc:
        raise ValueError("Evaluation is missing required fields or provenance") from exc
