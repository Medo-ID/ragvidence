"""Deterministic maximum marginal relevance with independently inspectable scores."""

import time

import numpy as np

from ragvidence.models import MMRConfig, RetrievalHit, StageTrace
from ragvidence.providers.vectors import document_vectors, query_vector


def select_mmr(
    hits: list[RetrievalHit], vectors, query, *, lambda_mult: float, k: int
) -> list[RetrievalHit]:
    if not 0 <= lambda_mult <= 1 or k < 1:
        raise ValueError("MMR requires lambda in [0,1] and positive k")
    if not hits:
        return []
    if len({hit.source_unit_id for hit in hits}) != len(hits):
        raise ValueError("MMR candidates must be unique")
    matrix = document_vectors(vectors, len(hits)).astype(np.float64)
    query = query_vector(query, matrix.shape[1]).astype(np.float64)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    query /= np.linalg.norm(query)
    relevance = matrix @ query
    remaining, results = list(range(len(hits))), []
    redundancy = None
    for _ in range(min(k, len(hits))):
        penalties = redundancy if redundancy is not None else np.zeros(len(hits))
        objectives = lambda_mult * relevance - (1 - lambda_mult) * penalties
        # max() keeps the first candidate on equal objectives, including lambda=0.
        index = max(remaining, key=lambda item: objectives[item])
        objective, penalty = float(objectives[index]), float(penalties[index])
        hit = hits[index]
        results.append(
            hit.model_copy(
                update={
                    "rank": len(results) + 1,
                    "score": objective,
                    "metadata": {
                        **hit.metadata,
                        "mmr": {
                            "input_rank": hit.rank,
                            "input_score": hit.score,
                            "relevance": float(relevance[index]),
                            "redundancy": penalty,
                            "objective": objective,
                        },
                    },
                }
            )
        )
        remaining.remove(index)
        similarity = matrix @ matrix[index]
        redundancy = similarity if redundancy is None else np.maximum(redundancy, similarity)
    return results


def diversify_hits(question: str, hits: list[RetrievalHit], model, config: MMRConfig):
    started = time.perf_counter()
    pool = hits[: config.candidates]
    selected = (
        select_mmr(
            pool,
            model.vectors_for([hit.source_unit_id for hit in pool]),
            model.encode_query(question),
            lambda_mult=config.lambda_mult,
            k=len(pool),
        )
        if pool
        else []
    )
    return selected, StageTrace(
        name="mmr",
        hits=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        details={
            "query": question,
            "lambda": config.lambda_mult,
            "candidate_limit": config.candidates,
            "input_ids": [hit.source_unit_id for hit in pool],
            "embedding_identity": model.embedding_identity if model else None,
            "index_cache": "warm_vectors"
            if model and model.cache_hit
            else "cold_vectors"
            if model
            else "not_applicable",
            "objective": "lambda*cos(query,candidate) - (1-lambda)*max_cos(candidate,selected)",
            "first_redundancy": 0,
            "ties": "input order",
        },
    )
