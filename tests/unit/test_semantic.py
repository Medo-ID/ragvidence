from pathlib import Path

import numpy as np
import pytest

from ragvidence.models import SourceUnit
from ragvidence.representation import build_records
from ragvidence.strategies.semantic import SemanticStrategy


class FakeProvider:
    model_name = "fake-v1"

    def __init__(self) -> None:
        self.document_calls = 0

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        self.document_calls += 1
        return np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray([1.0, 0.0], dtype=np.float32)


def _records():
    sources = [
        SourceUnit(source_unit_id="S-1", document_id="D", body="alpha", evidence_ids={"E-1"}),
        SourceUnit(source_unit_id="S-2", document_id="D", body="beta", evidence_ids={"E-2"}),
    ]
    return build_records(sources, "body")


def test_semantic_search_ranks_by_cosine_similarity(tmp_path: Path) -> None:
    provider = FakeProvider()
    strategy = SemanticStrategy(cache_dir=tmp_path, provider=provider)
    strategy.index(_records())
    hits = strategy.search("alpha concept", k=2)
    assert [hit.source_unit_id for hit in hits] == ["S-1", "S-2"]
    assert hits[0].score == 1.0


def test_semantic_index_reuses_local_cache(tmp_path: Path) -> None:
    first_provider = FakeProvider()
    first = SemanticStrategy(cache_dir=tmp_path, provider=first_provider)
    first.index(_records())
    assert first_provider.document_calls == 1
    assert first.cache_hit is False
    second_provider = FakeProvider()
    second = SemanticStrategy(cache_dir=tmp_path, provider=second_provider)
    second.index(_records())
    assert second_provider.document_calls == 0
    assert second.cache_hit is True


def test_deleted_embedding_cache_is_rebuilt_without_changing_ranking(tmp_path):
    first = SemanticStrategy(cache_dir=tmp_path / "vectors", provider=FakeProvider())
    first.index(_records())
    expected = first.search("alpha concept", k=2)
    for artifact in (tmp_path / "vectors").iterdir():
        artifact.unlink()
    (tmp_path / "vectors").rmdir()
    provider = FakeProvider()
    rebuilt = SemanticStrategy(cache_dir=tmp_path / "vectors", provider=provider)
    rebuilt.index(_records())
    assert provider.document_calls == 1
    assert rebuilt.cache_hit is False
    assert rebuilt.search("alpha concept", k=2) == expected


@pytest.mark.parametrize(
    "vectors",
    [
        [[0, 0], [1, 0]],
        [[float("nan"), 1], [1, 0]],
        [[float("inf"), 0], [1, 0]],
        [[1], [1, 0]],
        [[1, 0]],
        [[True, False], [False, True]],
        [["1", "0"], ["0", "1"]],
    ],
)
def test_invalid_document_vectors_are_rejected(vectors):
    class InvalidProvider(FakeProvider):
        def embed_documents(self, texts):
            return vectors

    with pytest.raises(RuntimeError):
        SemanticStrategy(provider=InvalidProvider()).index(_records())


@pytest.mark.parametrize("vector", [[0, 0], [float("nan"), 1], [1, 2, 3]])
def test_invalid_query_vector_is_rejected(vector):
    class InvalidQueryProvider(FakeProvider):
        def embed_query(self, text):
            return vector

    strategy = SemanticStrategy(provider=InvalidQueryProvider())
    strategy.index(_records())
    with pytest.raises(RuntimeError):
        strategy.search("query", k=2)


def test_provider_identity_prevents_cross_endpoint_cache_reuse(tmp_path):
    first_provider = FakeProvider()
    first_provider.cache_identity = {"model": "same-name", "endpoint": "A", "encoding": "v1"}
    first = SemanticStrategy(cache_dir=tmp_path, provider=first_provider)
    first.index(_records())
    second_provider = FakeProvider()
    second_provider.cache_identity = {"model": "same-name", "endpoint": "B", "encoding": "v1"}
    second = SemanticStrategy(cache_dir=tmp_path, provider=second_provider)
    second.index(_records())
    assert not second.cache_hit
    assert second_provider.document_calls == 1


def test_corrupted_embedding_cache_does_not_silently_produce_a_ranking(tmp_path):
    strategy = SemanticStrategy(cache_dir=tmp_path, provider=FakeProvider())
    strategy.index(_records())
    next(tmp_path.glob("*.npy")).write_bytes(b"not numpy")
    with pytest.raises(RuntimeError, match="Invalid semantic cache"):
        SemanticStrategy(cache_dir=tmp_path, provider=FakeProvider()).index(_records())
