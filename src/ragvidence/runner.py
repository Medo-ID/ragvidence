"""Reproducible experiment execution."""

from __future__ import annotations

import hashlib
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from ragvidence import __version__, pipeline
from ragvidence.artifacts import HASH_ALGORITHM, canonical_bytes, content_hash, write_json
from ragvidence.budgets import ContextCounter, select_context
from ragvidence.compression import compress_hits
from ragvidence.config import Settings
from ragvidence.context import context_fields
from ragvidence.data import canonical_dataset_bytes, load_dataset, validate_search_inputs
from ragvidence.filtering import eligible_sources, predicates_for
from ragvidence.models import (
    ExperimentRun,
    InputPreparation,
    QueryRun,
    RunManifest,
    SearchQuestion,
    SourceUnit,
    StageTrace,
    StrategyConfig,
)
from ragvidence.pipeline import (
    build_strategy,
    resolve_config,
)
from ragvidence.provenance import (
    configuration_identity,
    corpus_identity,
    question_identity,
    reference_identity,
    representation_identity,
)
from ragvidence.representation import build_records
from ragvidence.reranking import FastEmbedReranker
from ragvidence.retrieval_stages import (
    candidate_depth,
    fuse_queries,
    rerank_candidates,
    search_queries,
)
from ragvidence.selection import diversify_hits
from ragvidence.transformations import TransformationError, rewrite_question


def run_experiment(dataset: Path, config: StrategyConfig) -> ExperimentRun:
    if config.compression:
        raise ValueError("Compression needs portable original-span references; use ragvi compress")
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
    if config.filters and config.filters.questions.keys() - {q.question_id for q in questions}:
        raise ValueError("Metadata filters reference unknown question IDs")
    config = resolve_config(config, settings)
    candidate_k = config.candidate_k or config.k
    # Retrieval sees text and IDs; evaluation evidence is attached only afterwards.
    search_sources = [source.model_copy(update={"evidence_ids": set()}) for source in sources]
    records = build_records(search_sources, config.representation)
    started = time.perf_counter()
    indexes = {}
    for question in questions:
        predicates = predicates_for(config.filters, question.question_id)
        key = content_hash(predicates)
        if key not in indexes:
            eligible = eligible_sources(search_sources, predicates)
            ids = {source.source_unit_id for source in eligible}
            filtered = [record for record in records if record.source.source_unit_id in ids]
            strategy = build_strategy(config, cache_dir, settings) if filtered else None
            if strategy:
                strategy.index(filtered)
            indexes[key] = (strategy, ids)
    eligible_union = set().union(*(ids for _, ids in indexes.values()))
    diversity = (
        pipeline.semantic_strategy(config, cache_dir, settings)
        if eligible_union and config.mmr
        else None
    )
    if diversity:
        diversity.index(
            [record for record in records if record.source.source_unit_id in eligible_union]
        )
    reranker = (
        FastEmbedReranker(config.reranker_model, cache_dir=cache_dir / "models")
        if questions and config.reranker_model
        else None
    )
    index_ms = (time.perf_counter() - started) * 1000 if questions else None
    texts = {record.source.source_unit_id: record.searchable_text for record in records}
    sources_by_id = {source.source_unit_id: source for source in sources}
    counter = ContextCounter(config.tokenizer_file, config.tokenizer_hash)
    query_runs = []
    for question in questions:
        query_started = time.perf_counter()
        predicates = predicates_for(config.filters, question.question_id)
        strategy, eligible_ids = indexes[content_hash(predicates)]
        stages = []
        if config.filters:
            stages.append(
                StageTrace(
                    name="metadata_filter",
                    details={
                        "predicates": [predicate.model_dump() for predicate in predicates],
                        "policy": "conjunction-before-ranking-v1",
                        "missing_fields": "exclude",
                        "input_count": len(search_sources),
                        "eligible_count": len(eligible_ids),
                        "eligible_ids": [
                            s.source_unit_id
                            for s in search_sources
                            if s.source_unit_id in eligible_ids
                        ],
                    },
                )
            )
        queries = [question.question]
        if config.rewrite:
            try:
                queries, rewrite_trace = rewrite_question(
                    question.question, config.rewrite, settings
                )
            except TransformationError as exc:
                exc.question_id = question.question_id
                raise
            stages.append(rewrite_trace)
        queries = list(
            dict.fromkeys(
                [
                    *queries,
                    *(
                        variant.strip()
                        for variant in config.query_variants.get(question.question_id, [])
                    ),
                ]
            )
        )
        depth = candidate_depth(config, len(queries))
        rankings, retrieval_traces = search_queries(strategy, queries, depth, eligible_ids)
        stages.extend(retrieval_traces)
        hits, fusion_traces = fuse_queries(rankings, config, depth)
        stages.extend(fusion_traces)
        if reranker:
            hits, rerank_trace = rerank_candidates(
                question.question, hits, reranker, texts, config.rerank_k or candidate_k
            )
            stages.append(rerank_trace)
        if any(hit.source_unit_id not in eligible_ids for hit in hits):
            raise ValueError("Candidate selection returned an unknown or excluded source ID")
        if config.mmr:
            hits, diversity_trace = diversify_hits(question.question, hits, diversity, config.mmr)
            stages.append(diversity_trace)
        if config.compression:
            try:
                hits, compression_trace = compress_hits(
                    question.question, hits, sources_by_id, config.compression, settings
                )
            except TransformationError as exc:
                exc.question_id = question.question_id
                raise
            stages.append(compression_trace)
        stage_started = time.perf_counter()
        hits, measurement = select_context(
            hits, sources_by_id, k=config.k, budget=config.context_budget, counter=counter
        )
        stages.append(
            StageTrace(
                name="context_selection",
                hits=hits,
                elapsed_ms=(time.perf_counter() - stage_started) * 1000,
                details=measurement,
            )
        )
        hits = [
            hit.model_copy(
                update={
                    "evidence_ids": set()
                    if hit.context_spans is not None
                    else sources_by_id[hit.source_unit_id].evidence_ids
                }
            )
            for hit in hits
        ]
        context = context_fields(hits, sources_by_id)
        query_runs.append(
            QueryRun(
                question_id=question.question_id,
                hits=hits,
                query_time_ms=(time.perf_counter() - query_started) * 1000,
                search_queries=queries,
                stages=stages,
                context_measurement=measurement,
                **context,
            )
        )
    warnings = []
    if config.strategy in {"semantic", "hybrid"} or config.reranker_model or config.mmr:
        warnings.append(
            "Model adapters may truncate embedding/reranking inputs; exact truncation "
            "counts are unavailable. Evidence scores describe returned original text, "
            "not proof every character was encoded by a model."
        )
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
    if config.rewrite:
        warnings.append(
            "Automatic query variants can drift from the original intent; "
            "evaluation uses the original question."
        )
    if config.compression:
        warnings.append(
            "Extractive compression can remove required facts or qualifications; "
            "evidence is rescored from only the returned spans."
        )
    if config.rewrite or (config.compression and config.compression.mode == "model"):
        warnings.append(
            "Transformation model token usage and input truncation are unknown; "
            "exact prompts and bounded outputs are retained."
        )
    if config.mmr or config.rewrite or (config.compression and config.compression.mode == "model"):
        warnings.append(
            "Model names and endpoints may resolve to changed weights. Runtime model "
            "revisions are not independently verified by each run; recorded integration "
            "fingerprints apply only to those compatibility checks."
        )
    return ExperimentRun(
        manifest=build_manifest(
            sources,
            questions,
            config,
            dataset_hash=dataset_hash,
            evaluation_level=evaluation_level,
            references_hash=references_hash,
            corpus_hash=corpus_hash,
            input_preparation=input_preparation,
            index_ms=index_ms,
            warnings=warnings,
        ),
        queries=query_runs,
    )


def build_manifest(
    sources: list[SourceUnit],
    questions: list[SearchQuestion],
    config: StrategyConfig,
    *,
    dataset_hash: str,
    evaluation_level: str,
    references_hash: str | None = None,
    corpus_hash: str | None = None,
    input_preparation: InputPreparation | None = None,
    index_ms: float | None = None,
    warnings: list[str] | None = None,
) -> RunManifest:
    """Record common provenance for executed and imported portable runs."""
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_key = canonical_bytes(
        {"config": config, "dataset_hash": dataset_hash, "timestamp": datetime.now(UTC).isoformat()}
    )
    return RunManifest(
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
        warnings=warnings or [],
    )


def write_run(run: ExperimentRun, output: Path) -> None:
    write_json(output, run)
