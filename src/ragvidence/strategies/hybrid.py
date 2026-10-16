"""Rank fusion shared by hybrid and multi-query retrieval."""

import math
import time
from collections.abc import Sequence

from ragvidence.models import RetrievalHit, StageTrace
from ragvidence.representation import RetrievalRecord
from ragvidence.strategies.base import RetrievalStrategy


def fuse_rankings(
    rankings: Sequence[Sequence[RetrievalHit]],
    *,
    k: int,
    constant: int = 60,
    weights: Sequence[float] | None = None,
) -> list[RetrievalHit]:
    """Weighted RRF with one contribution per source per list and stable ties."""
    if k < 1 or constant < 0:
        raise ValueError("k must be positive and the RRF constant nonnegative")
    weights = list(weights) if weights is not None else [1.0] * len(rankings)
    if len(weights) != len(rankings) or any(
        not math.isfinite(weight) or weight <= 0 for weight in weights
    ):
        raise ValueError("Each ranking needs a finite positive weight")
    scores: dict[str, float] = {}
    originals: dict[str, RetrievalHit] = {}
    contributions: dict[str, list[dict]] = {}
    for list_index, (hits, weight) in enumerate(zip(rankings, weights, strict=True)):
        seen = set()
        for hit in hits:
            source_id = hit.source_unit_id
            if source_id in seen:
                continue
            seen.add(source_id)
            originals.setdefault(source_id, hit)
            scores[source_id] = scores.get(source_id, 0.0) + weight / (constant + hit.rank)
            contributions.setdefault(source_id, []).append(
                {
                    "list": list_index,
                    "rank": hit.rank,
                    "score": hit.score,
                    "weight": weight,
                    "source_unit_id": source_id,
                    "metadata": hit.metadata,
                }
            )
    ordered = sorted(scores, key=lambda source_id: -scores[source_id])[:k]
    return [
        originals[source_id].model_copy(
            update={
                "rank": rank,
                "score": scores[source_id],
                "metadata": {
                    **originals[source_id].metadata,
                    "rrf_contributions": contributions[source_id],
                },
            }
        )
        for rank, source_id in enumerate(ordered, start=1)
    ]


class HybridStrategy:
    def __init__(
        self,
        lexical: RetrievalStrategy,
        semantic: RetrievalStrategy,
        *,
        candidate_k: int,
        lexical_weight: float = 0.5,
        constant: int = 60,
        fixed_depth: bool = False,
    ) -> None:
        self.lexical, self.semantic = lexical, semantic
        self.fixed_depth = fixed_depth
        self.last_trace: list[StageTrace] = []
        self.candidate_k, self.lexical_weight, self.constant = (
            candidate_k,
            lexical_weight,
            constant,
        )

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        self.lexical.index(records)
        self.semantic.index(records)

    def search(self, query: str, *, k: int) -> list[RetrievalHit]:
        depth = self.candidate_k if self.fixed_depth else max(k, self.candidate_k)
        rankings = []
        self.last_trace = []
        for name, strategy in (("lexical", self.lexical), ("dense", self.semantic)):
            start = time.perf_counter()
            hits = strategy.search(query, k=depth)
            rankings.append(hits)
            self.last_trace.append(
                StageTrace(
                    name=name,
                    elapsed_ms=(time.perf_counter() - start) * 1000,
                    hits=hits,
                    details={"query": query, "limit": depth},
                )
            )
        start = time.perf_counter()
        fused = fuse_rankings(
            rankings,
            k=k,
            constant=self.constant,
            weights=[self.lexical_weight, 1 - self.lexical_weight],
        )
        self.last_trace.append(
            StageTrace(
                name="hybrid_fusion",
                elapsed_ms=(time.perf_counter() - start) * 1000,
                hits=fused,
                details={"query": query, "limit": k},
            )
        )
        return fused
