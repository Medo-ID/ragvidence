"""Reproducible experiment execution."""

from __future__ import annotations

import hashlib
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from ragvidence import __version__
from ragvidence.artifacts import HASH_ALGORITHM, canonical_bytes, write_json
from ragvidence.config import Settings
from ragvidence.context import context_fields
from ragvidence.data import canonical_dataset_bytes, load_dataset, validate_search_inputs
from ragvidence.models import (
    ExperimentRun,
    InputPreparation,
    QueryRun,
    RunManifest,
    SearchQuestion,
    SourceUnit,
    StrategyConfig,
)
from ragvidence.pipeline import build_strategy, resolve_config
from ragvidence.provenance import (
    configuration_identity,
    corpus_identity,
    question_identity,
    reference_identity,
    representation_identity,
)
from ragvidence.representation import build_records
from ragvidence.reranking import FastEmbedReranker
from ragvidence.strategies.hybrid import fuse_rankings


def run_experiment(dataset: Path, config: StrategyConfig) -> ExperimentRun:
    sources, questions = load_dataset(dataset)
    return execute_retrieval(
        sources,
        [SearchQuestion(question_id=q.question_id, question=q.question) for q in questions],
        config,
        cache_dir=dataset / ".ragvidence-cache",
        settings=Settings(),
        dataset_hash=hashlib.sha256(canonical_dataset_bytes(sources, questions)).hexdigest(),
        evaluation_level="reviewed_evaluation",
        references_hash=reference_identity(sources, questions),
    )


def execute_retrieval(
    sources: list[SourceUnit],
    questions: list[SearchQuestion],
    config: StrategyConfig,
    *,
    cache_dir: Path,
    settings: Settings,
    dataset_hash: str,
    evaluation_level: str = "retrieval_inspection",
    references_hash: str | None = None,
    corpus_hash: str | None = None,
    input_preparation: InputPreparation | None = None,
) -> ExperimentRun:
    """Execute retrieval without exposing evaluation labels to pipeline stages."""
    validate_search_inputs(sources, questions)
    unknown = config.query_variants.keys() - {question.question_id for question in questions}
    if unknown:
        raise ValueError(f"Query variants reference unknown question IDs: {sorted(unknown)}")
    config = resolve_config(config, settings)
    candidate_k = config.candidate_k or config.k
    # Retrieval sees text and IDs; evaluation evidence is attached only afterwards.
    search_sources = [source.model_copy(update={"evidence_ids": set()}) for source in sources]
    records = build_records(search_sources, config.representation)
    started = time.perf_counter()
    strategy = build_strategy(config, cache_dir, settings) if questions else None
    if strategy:
        strategy.index(records)
    reranker = (
        FastEmbedReranker(config.reranker_model) if questions and config.reranker_model else None
    )
    index_ms = (time.perf_counter() - started) * 1000 if strategy is not None else None
    texts = {record.source.source_unit_id: record.searchable_text for record in records}
    sources_by_id = {source.source_unit_id: source for source in sources}
    query_runs = []
    for question in questions:
        query_started = time.perf_counter()
        queries = list(
            dict.fromkeys(
                [
                    question.question,
                    *(
                        variant.strip()
                        for variant in config.query_variants.get(question.question_id, [])
                    ),
                ]
            )
        )
        depth = candidate_k if reranker or len(queries) > 1 else config.k
        rankings = [strategy.search(query, k=depth) for query in queries]
        hits = (
            fuse_rankings(rankings, k=depth, constant=config.rrf_constant)
            if len(rankings) > 1
            else rankings[0]
        )
        if reranker:
            hits = reranker.rerank(question.question, hits, texts, k=config.k)
        hits = hits[: config.k]
        if any(hit.source_unit_id not in sources_by_id for hit in hits):
            raise ValueError("Retriever returned an unknown source ID")
        hits = [
            hit.model_copy(update={"evidence_ids": sources_by_id[hit.source_unit_id].evidence_ids})
            for hit in hits
        ]
        context = context_fields(hits, sources_by_id)
        query_runs.append(
            QueryRun(
                question_id=question.question_id,
                hits=hits,
                query_time_ms=(time.perf_counter() - query_started) * 1000,
                search_queries=queries,
                **context,
            )
        )
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_key = canonical_bytes(
        {"config": config, "dataset_hash": dataset_hash, "timestamp": datetime.now(UTC).isoformat()}
    )
    warnings = []
    if config.child_splitter != "none":
        warnings.append(
            "Child retrieval returns full parent source units. Evidence metrics describe "
            "parent context; they do not establish that the matching child contains every fact. "
            "Child candidate limits can return fewer than k unique parents."
        )
    if config.representation == "contextual":
        warnings.append("Context prefixes are supplied by the dataset and require human review.")
    if config.query_variants:
        warnings.append(
            "Query variants are supplied in the configuration. Keep held-out questions "
            "independent of evidence labels when preparing variants."
        )
    return ExperimentRun(
        manifest=RunManifest(
            schema_version=2,
            hash_algorithm=HASH_ALGORITHM,
            evaluation_level=evaluation_level,
            run_id=hashlib.sha256(run_key).hexdigest()[:12],
            created_at=timestamp,
            product_version=__version__,
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            dataset_hash=dataset_hash,
            corpus_hash=corpus_hash or corpus_identity(sources),
            questions_hash=question_identity(questions),
            references_hash=references_hash,
            representation_hash=representation_identity(sources, config),
            configuration_hash=configuration_identity(config, input_preparation),
            input_preparation=input_preparation,
            config=config,
            index_time_ms=index_ms,
            warnings=warnings,
        ),
        queries=query_runs,
    )


def write_run(run: ExperimentRun, output: Path) -> None:
    write_json(output, run)
