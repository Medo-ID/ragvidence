"""Local dense retrieval with a reusable provider-independent vector cache."""

import io
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

import numpy as np

from ragvidence.artifacts import content_hash, write_bytes
from ragvidence.models import RetrievalHit
from ragvidence.providers import EmbeddingProvider, FastEmbedProvider
from ragvidence.providers.vectors import document_vectors, query_vector
from ragvidence.representation import RetrievalRecord


class SemanticStrategy:
    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        *,
        cache_dir: Path | None = None,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.model_name = model_name
        self._provider = provider or FastEmbedProvider(
            model_name, cache_dir=cache_dir.parent / "models" if cache_dir else None
        )
        self._cache_dir = cache_dir
        self._records: list[RetrievalRecord] = []
        self._vectors: np.ndarray | None = None
        self.cache_hit = False

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        self._records = list(records)
        self.cache_hit = False
        texts = [item.searchable_text for item in self._records]
        cache_path = self._cache_path(texts)
        if cache_path is not None and cache_path.is_file():
            try:
                with cache_path.open("rb") as handle:
                    vectors = document_vectors(np.load(handle, allow_pickle=False), len(texts))
            except (OSError, ValueError, RuntimeError) as exc:
                raise RuntimeError(f"Invalid semantic cache: {cache_path}") from exc
            self.cache_hit = True
        else:
            vectors = document_vectors(self._provider.embed_documents(texts), len(texts))
            if cache_path is not None:
                buffer = io.BytesIO()
                np.save(buffer, vectors, allow_pickle=False)
                # A concurrent indexer may publish this immutable cache first.
                with suppress(FileExistsError):
                    write_bytes(cache_path, buffer.getvalue())
        self._vectors = _normalize(np.asarray(vectors, dtype=np.float32))

    def search(self, query: str, *, k: int) -> list[RetrievalHit]:
        if self._vectors is None:
            raise RuntimeError("index() must be called before search()")
        raw_query = query_vector(self._provider.embed_query(query), self._vectors.shape[1])
        normalized_query = _normalize(raw_query[None, :])[0]
        scores = self._vectors @ normalized_query
        indexes = np.argsort(-scores, kind="stable")[: min(k, len(scores))]
        return [
            RetrievalHit(
                source_unit_id=self._records[int(index)].source.source_unit_id,
                rank=rank,
                score=float(scores[int(index)]),
                evidence_ids=self._records[int(index)].source.evidence_ids,
                preview=self._records[int(index)].searchable_text[:240],
                metadata={"document_id": self._records[int(index)].source.document_id},
            )
            for rank, index in enumerate(indexes, start=1)
        ]

    def _cache_path(self, texts: list[str]) -> Path | None:
        if self._cache_dir is None:
            return None
        identity = getattr(
            self._provider,
            "cache_identity",
            {
                "adapter": f"{type(self._provider).__module__}.{type(self._provider).__qualname__}",
                "model": self._provider.model_name,
            },
        )
        return self._cache_dir / f"{content_hash({'identity': identity, 'texts': texts})}.npy"


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors.astype(np.float64), axis=1, keepdims=True)
    return (vectors / norms).astype(np.float32)
