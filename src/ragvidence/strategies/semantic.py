"""Local dense retrieval with a reusable provider-independent vector cache."""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from ragvidence.models import RetrievalHit
from ragvidence.providers import EmbeddingProvider, FastEmbedProvider
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
        self._provider = provider or FastEmbedProvider(model_name)
        self._cache_dir = cache_dir
        self._records: list[RetrievalRecord] = []
        self._vectors: np.ndarray | None = None
        self.cache_hit = False

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        self._records = list(records)
        texts = [item.searchable_text for item in self._records]
        cache_path = self._cache_path(texts)
        if cache_path is not None and cache_path.is_file():
            with cache_path.open("rb") as handle:
                vectors = np.load(handle, allow_pickle=False)
            if vectors.ndim != 2 or vectors.shape[0] != len(texts):
                raise RuntimeError(f"Invalid semantic cache shape: {cache_path}")
            self.cache_hit = True
        else:
            vectors = self._provider.embed_documents(texts)
            if vectors.ndim != 2 or vectors.shape[0] != len(texts):
                raise RuntimeError("Embedding provider returned an invalid document matrix")
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                temporary = cache_path.with_suffix(".tmp")
                with temporary.open("wb") as handle:
                    np.save(handle, vectors, allow_pickle=False)
                temporary.replace(cache_path)
        self._vectors = _normalize(np.asarray(vectors, dtype=np.float32))

    def search(self, query: str, *, k: int) -> list[RetrievalHit]:
        if self._vectors is None:
            raise RuntimeError("index() must be called before search()")
        raw_query = np.asarray(self._provider.embed_query(query), dtype=np.float32)
        if raw_query.ndim != 1 or raw_query.shape[0] != self._vectors.shape[1]:
            raise RuntimeError("Embedding provider returned an invalid query vector")
        query_vector = _normalize(raw_query[None, :])[0]
        scores = self._vectors @ query_vector
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
        payload = json.dumps(
            {"model": self._provider.model_name, "texts": texts},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return self._cache_dir / f"{hashlib.sha256(payload).hexdigest()}.npy"


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)
