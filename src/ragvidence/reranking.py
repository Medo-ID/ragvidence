"""Optional local cross-encoder reranking of retrieved candidates."""

import math
from pathlib import Path

from ragvidence.models import RetrievalHit


class FastEmbedReranker:
    def __init__(self, model_name: str, *, cache_dir: Path | None = None) -> None:
        try:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
        except ImportError as exc:
            raise RuntimeError("Local reranking requires 'ragvidence[semantic]'") from exc
        self._model = TextCrossEncoder(
            model_name=model_name,
            **({"cache_dir": str(cache_dir)} if cache_dir is not None else {}),
        )

    def rerank(
        self, query: str, hits: list[RetrievalHit], texts: dict[str, str], *, k: int
    ) -> list[RetrievalHit]:
        if not hits:
            return []
        scores = [
            float(score)
            for score in self._model.rerank(query, [texts[hit.source_unit_id] for hit in hits])
        ]
        if len(scores) != len(hits) or any(not math.isfinite(score) for score in scores):
            raise RuntimeError("Reranker returned invalid scores")
        ordered = sorted(zip(hits, scores, strict=True), key=lambda item: -item[1])[:k]
        return [
            hit.model_copy(
                update={
                    "rank": rank,
                    "score": score,
                    "metadata": {
                        **hit.metadata,
                        "before_rerank_rank": hit.rank,
                        "before_rerank_score": hit.score,
                    },
                }
            )
            for rank, (hit, score) in enumerate(ordered, start=1)
        ]
