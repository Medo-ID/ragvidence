"""Check M6 selections against source scope and retained transformation evidence."""

import math

from ragvidence.compression import (
    COMPRESSION_PROMPT,
    compression_input,
    lexical_spans,
    parse_selections,
    validate_spans,
)
from ragvidence.filtering import eligible_sources, predicates_for
from ragvidence.models import QueryRun, SearchQuestion, SourceUnit, StrategyConfig
from ragvidence.transformations import REWRITE_PROMPT, model_details, parse_rewrite, rewrite_input


def _one_stage(query: QueryRun, name: str):
    matches = [stage for stage in query.stages if stage.name == name]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {name} stage")
    return matches[0]


def validate_rewriting(query: QueryRun, question: SearchQuestion, config: StrategyConfig):
    stage = _one_stage(query, "query_rewriting")
    details = stage.details
    rewrite = config.rewrite
    if details.get("state") == "fallback_original":
        if rewrite.failure != "original":
            raise ValueError("Undeclared rewriting fallback")
        queries = [question.question]
    else:
        queries = parse_rewrite(details.get("raw_output"), question.question, rewrite)
        expected = model_details(
            rewrite, REWRITE_PROMPT, rewrite_input(question.question, rewrite.count)
        )
        if any(details.get(key) != value for key, value in expected.items()):
            raise ValueError("Rewrite prompt/model evidence does not match the original question")
    if details.get("queries") != queries or query.search_queries != list(
        dict.fromkeys(
            [
                *queries,
                *(q.strip() for q in config.query_variants.get(question.question_id, [])),
            ]
        )
    ):
        raise ValueError("Recorded search queries do not match the query transformation")


def validate_compression(
    query: QueryRun, question: SearchQuestion, config: StrategyConfig, sources: dict
):
    stage = _one_stage(query, "compression")
    details = stage.details
    compression = config.compression
    input_ids = details.get("input_ids", [])
    if len(input_ids) != len(set(input_ids)) or any(key not in sources for key in input_ids):
        raise ValueError("Compression input IDs must be known and unique")
    state = details.get("state")
    if state == "empty_input":
        if input_ids or stage.hits or query.hits:
            raise ValueError("Empty compression cannot return context")
        return
    if state == "fallback_original":
        if compression.failure != "original" or any(
            h.context_spans is not None for h in stage.hits
        ):
            raise ValueError("Undeclared compression fallback")
    elif state == "complete":
        if compression.mode == "sentences":
            selections = {
                key: lexical_spans(question.question, sources[key].body, compression.max_spans)
                for key in input_ids
            }
        else:
            selections = parse_selections(details.get("raw_output"), input_ids)
            expected = model_details(
                compression,
                COMPRESSION_PROMPT,
                compression_input(question.question, input_ids, sources, compression.max_spans),
            )
            if any(details.get(key) != value for key, value in expected.items()):
                raise ValueError("Compression prompt/model evidence does not match original inputs")
        for key, spans in selections.items():
            validate_spans(spans, sources[key].body, limit=compression.max_spans)
        if details.get("selections") != {
            key: [span.model_dump() for span in spans] for key, spans in selections.items()
        }:
            raise ValueError("Recorded compression selections differ from transformation output")
        expected = [(key, spans) for key, spans in selections.items() if spans]
        if [(h.source_unit_id, h.context_spans) for h in stage.hits] != expected:
            raise ValueError("Compression hits differ from selected original spans")
    else:
        raise ValueError("Unknown compression state")
    by_id = {hit.source_unit_id: hit for hit in stage.hits}
    for hit in query.hits:
        if (
            hit.source_unit_id not in by_id
            or hit.context_spans != by_id[hit.source_unit_id].context_spans
        ):
            raise ValueError("Returned extracts differ from compression provenance")


def validate_stage_scope(
    query: QueryRun, question: SearchQuestion, config: StrategyConfig, sources: list[SourceUnit]
):
    by_id = {source.source_unit_id: source for source in sources}
    eligible = eligible_sources(sources, predicates_for(config.filters, question.question_id))
    ids = {source.source_unit_id for source in eligible}
    if config.filters:
        stage = _one_stage(query, "metadata_filter")
        if stage.details.get("eligible_ids") != [source.source_unit_id for source in eligible]:
            raise ValueError("Metadata scope does not match source predicates")
    if any(hit.source_unit_id not in ids for hit in query.hits):
        raise ValueError("Returned context escaped its metadata scope")
    if config.rewrite:
        validate_rewriting(query, question, config)
    if config.mmr:
        validate_mmr(query, question, config)
    if config.compression:
        validate_compression(query, question, config, by_id)
        if any(
            key not in ids for key in _one_stage(query, "compression").details.get("input_ids", [])
        ):
            raise ValueError("Compression candidates escaped their metadata scope")


def validate_mmr(query: QueryRun, question: SearchQuestion, config: StrategyConfig):
    stage = _one_stage(query, "mmr")
    preceding = query.stages[: query.stages.index(stage)]
    candidates = next(
        s.hits
        for s in reversed(preceding)
        if s.name in {"retrieval", "reranking", "multi_query_fusion"}
    )[: config.mmr.candidates]
    ids = [hit.source_unit_id for hit in candidates]
    if stage.details.get("input_ids") != ids or stage.details.get("query") != question.question:
        raise ValueError("MMR provenance differs from original question/candidate pool")
    if len(stage.hits) != len(ids) or {h.source_unit_id for h in stage.hits} != set(ids):
        raise ValueError("MMR must only reorder its bounded candidate pool")
    originals = {hit.source_unit_id: hit for hit in candidates}
    for rank, hit in enumerate(stage.hits, 1):
        values = hit.metadata.get("mmr", {})
        relevance, redundancy = values.get("relevance"), values.get("redundancy")
        if any(
            type(value) not in {int, float} or not math.isfinite(value) or abs(value) > 1.00001
            for value in (relevance, redundancy)
        ):
            raise ValueError("MMR cosine provenance is invalid")
        objective = config.mmr.lambda_mult * relevance - (1 - config.mmr.lambda_mult) * redundancy
        original = originals[hit.source_unit_id]
        if (
            hit.rank != rank
            or not math.isclose(hit.score, objective, abs_tol=1e-9)
            or values.get("objective") != hit.score
            or values.get("input_rank") != original.rank
            or values.get("input_score") != original.score
            or (rank == 1 and redundancy != 0)
        ):
            raise ValueError("MMR scores do not match their recorded objective")
    selected = {hit.source_unit_id: hit for hit in stage.hits}
    if any(
        hit.source_unit_id not in selected or hit.score != selected[hit.source_unit_id].score
        for hit in query.hits
    ):
        raise ValueError("Final ranking differs from recorded MMR selection")
