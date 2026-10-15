"""Shared run validation before evaluation or answer inspection."""

from __future__ import annotations

import hashlib
import json
from collections import Counter

from ragvidence.context import context_fields
from ragvidence.data import DatasetError, canonical_dataset_bytes, validate_dataset
from ragvidence.models import ExperimentRun, QuestionCase, SourceUnit
from ragvidence.provenance import (
    configuration_identity,
    corpus_identity,
    question_identity,
    reference_identity,
    representation_identity,
)


def validate_run(
    run: ExperimentRun, sources: list[SourceUnit], questions: list[QuestionCase]
) -> None:
    # Revalidate even objects mutated after initial construction.
    run = ExperimentRun.model_validate(run.model_dump())
    validate_dataset(sources, questions)
    if run.manifest.evaluation_level != "reviewed_evaluation":
        raise DatasetError("Scored evaluation requires reviewed questions and evidence")
    if run.manifest.hash_algorithm == "canonical-json-v1":
        expected = hashlib.sha256(canonical_dataset_bytes(sources, questions)).hexdigest()
    else:
        # Legacy artifacts may be read, but only scored when their recorded hash
        # can actually be reproduced. Do not silently relabel them as version 2.
        raw = {
            "sources": [item.model_dump(mode="json") for item in sources],
            "questions": [item.model_dump(mode="json") for item in questions],
        }
        expected = hashlib.sha256(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    if run.manifest.dataset_hash != expected:
        raise DatasetError("Run dataset hash does not match this dataset; rerun the experiment")
    if run.manifest.schema_version == 2:
        identities = {
            "corpus_hash": corpus_identity(sources),
            "questions_hash": question_identity(questions),
            "references_hash": reference_identity(sources, questions),
            "configuration_hash": configuration_identity(
                run.manifest.config, run.manifest.input_preparation
            ),
        }
        if run.manifest.config.strategy != "imported":
            identities["representation_hash"] = representation_identity(
                sources, run.manifest.config
            )
        for field, identity in identities.items():
            if getattr(run.manifest, field) != identity:
                raise DatasetError(f"Run {field} does not match its declared inputs")
    counts = Counter(query.question_id for query in run.queries)
    required_ids = {question.question_id for question in questions}
    if set(counts) != required_ids or any(count != 1 for count in counts.values()):
        raise DatasetError("Run must contain every dataset question exactly once")
    source_by_id = {source.source_unit_id: source for source in sources}
    for query in run.queries:
        if len(query.hits) > run.manifest.config.k:
            raise DatasetError(f"{query.question_id}: hits exceed retrieval depth k")
        seen = set()
        for rank, hit in enumerate(query.hits, start=1):
            if hit.rank != rank:
                raise DatasetError(f"{query.question_id}: ranks must be contiguous from 1")
            if hit.source_unit_id in seen:
                raise DatasetError(f"{query.question_id}: duplicate source in results")
            seen.add(hit.source_unit_id)
            source = source_by_id.get(hit.source_unit_id)
            if source is None:
                raise DatasetError(f"{query.question_id}: unknown source {hit.source_unit_id}")
            if hit.evidence_ids != source.evidence_ids:
                raise DatasetError(f"{query.question_id}: recorded evidence does not match source")
        if run.manifest.schema_version == 2:
            expected_context = context_fields(query.hits, source_by_id)
            for field, expected_value in expected_context.items():
                if getattr(query, field) != expected_value:
                    raise DatasetError(
                        f"{query.question_id}: recorded {field} does not match sources"
                    )
