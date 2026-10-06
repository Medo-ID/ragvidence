from pathlib import Path

import numpy as np

from raglab.models import SourceUnit
from raglab.representation import build_records
from raglab.strategies.semantic import SemanticStrategy


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
