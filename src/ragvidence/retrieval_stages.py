"""Candidate ranking and fusion stages shared by all retrieval techniques."""

import time

from ragvidence.models import RetrievalHit, StageTrace, StrategyConfig
from ragvidence.pipeline import runtime_versions, vector_cache_state
from ragvidence.strategies.hybrid import fuse_rankings


def candidate_depth(config: StrategyConfig, query_count: int) -> int:
    extended = (
        config.reranker_model
        or query_count > 1
        or config.context_budget
        or config.mmr
        or config.compression
    )
    if config.query_k is not None:
        return config.query_k
    depth = (config.candidate_k or config.k) if extended else config.k
    return max(depth, config.mmr.candidates) if config.mmr else depth


def search_queries(strategy, queries: list[str], depth: int, eligible_ids: set[str]):
    rankings, stages = [], []
    for query in queries:
        started = time.perf_counter()
        ranking = strategy.search(query, k=depth) if strategy else []
        if any(hit.source_unit_id not in eligible_ids for hit in ranking):
            raise ValueError("Retriever returned a source excluded by metadata predicates")
        rankings.append(ranking)
        stages.extend(getattr(strategy, "last_trace", []))
        stages.append(
            StageTrace(
                name="retrieval",
                hits=ranking,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                details={
                    "query": query,
                    "limit": depth,
                    "index_cache": vector_cache_state(strategy),
                    "model_cache": "unknown",
                    "runtime_versions": runtime_versions(),
                },
            )
        )
    return rankings, stages


def fuse_queries(rankings: list[list[RetrievalHit]], config: StrategyConfig, depth: int):
    if len(rankings) == 1:
        return rankings[0], []
    started = time.perf_counter()
    hits = fuse_rankings(rankings, k=depth, constant=config.rrf_constant)
    return hits, [
        StageTrace(
            name="multi_query_fusion", hits=hits, elapsed_ms=(time.perf_counter() - started) * 1000
        )
    ]


def rerank_candidates(question: str, hits: list[RetrievalHit], reranker, texts: dict, limit: int):
    started = time.perf_counter()
    pool = hits[:limit]
    # Some adapters cannot encode an empty batch; empty candidates remain empty.
    hits = reranker.rerank(question, pool, texts, k=len(pool)) if pool else []
    return hits, StageTrace(
        name="reranking",
        hits=hits,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        details={
            "query": question,
            "input_ids": [hit.source_unit_id for hit in pool],
            "limit": limit,
        },
    )
