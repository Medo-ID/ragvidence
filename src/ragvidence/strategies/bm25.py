"""Deterministic local BM25 retrieval."""

import re
from collections.abc import Sequence

import bm25s

from ragvidence.models import RetrievalHit
from ragvidence.representation import RetrievalRecord

TOKEN_PATTERN = re.compile(r"[^\W_]+(?:[._-][^\W_]+)*", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Preserve product identifiers and version-like tokens."""
    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text)]


class BM25Strategy:
    def __init__(self) -> None:
        self._records: list[RetrievalRecord] = []
        self._retriever: bm25s.BM25 | None = None

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        self._records = list(records)
        corpus_tokens = [tokenize(item.searchable_text) for item in self._records]
        if not any(corpus_tokens):
            raise ValueError("The input contains no searchable words for BM25")
        self._retriever = bm25s.BM25()
        self._retriever.index(corpus_tokens, show_progress=False)

    def search(self, query: str, *, k: int) -> list[RetrievalHit]:
        if self._retriever is None:
            raise RuntimeError("index() must be called before search()")
        limit = min(k, len(self._records))
        indexes, scores = self._retriever.retrieve([tokenize(query)], k=limit, show_progress=False)
        hits = []
        pairs = zip(indexes[0], scores[0], strict=True)
        for rank, (index, score) in enumerate(pairs, start=1):
            record = self._records[int(index)]
            hits.append(
                RetrievalHit(
                    source_unit_id=record.source.source_unit_id,
                    rank=rank,
                    score=float(score),
                    evidence_ids=record.source.evidence_ids,
                    preview=record.searchable_text[:240],
                    metadata={"document_id": record.source.document_id},
                )
            )
        return hits
