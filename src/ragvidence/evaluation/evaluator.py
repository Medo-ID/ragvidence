"""Compose evidence-level metrics into a reproducible evaluation result."""

from __future__ import annotations

from typing import Any

from ragvidence.artifacts import json_value
from ragvidence.evaluation.metrics import (
    evidence_coverage_at_k,
    first_relevant_rank,
    precision_at_k,
    reciprocal_rank,
    sufficient_evidence_at_k,
)
from ragvidence.models import ExperimentRun, QuestionCase, SourceUnit
from ragvidence.validation import validate_run


def evaluate_run(
    run: ExperimentRun, questions: list[QuestionCase], *, sources: list[SourceUnit]
) -> dict[str, Any]:
    validate_run(run, sources, questions)
    by_id = {item.question_id: item for item in questions}
    results = []
    for query in run.queries:
        question = by_id[query.question_id]
        ranking = [hit.evidence_ids for hit in query.hits]
        required = question.required_evidence_ids
        results.append(
            {
                "question_id": query.question_id,
                "question": question.question,
                "split": question.split,
                "answerable": question.answerable,
                "required_evidence_ids": sorted(required),
                "sufficient_evidence": sufficient_evidence_at_k(
                    required, ranking, run.manifest.config.k
                ),
                "evidence_coverage": evidence_coverage_at_k(
                    required, ranking, run.manifest.config.k
                ),
                "first_relevant_rank": first_relevant_rank(
                    required, ranking, run.manifest.config.k
                ),
                "reciprocal_rank": reciprocal_rank(required, ranking, run.manifest.config.k),
                "precision_at_k": precision_at_k(required, ranking, run.manifest.config.k),
                "hits": json_value(query.hits),
                "search_queries": query.search_queries,
                "returned_context_characters": query.returned_context_characters,
                "query_time_ms": query.query_time_ms,
            }
        )
    answerable = [item for item in results if item["answerable"]]
    successes = sum(item["sufficient_evidence"] is True for item in answerable)
    return {
        "schema_version": 2,
        "integrity": ("verified" if run.manifest.schema_version == 2 else "legacy_hash_matched"),
        "_validation": json_value({"sources": sources, "questions": questions, "run": run}),
        "manifest": run.manifest.model_dump(mode="json"),
        "summary": {
            "successful": successes,
            "answerable": len(answerable),
            "sufficient_evidence_rate": successes / len(answerable) if answerable else None,
        },
        "questions": results,
    }
