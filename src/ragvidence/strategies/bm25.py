"""Deterministic local BM25 retrieval."""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import numpy as np

from ragvidence.models import RetrievalHit
from ragvidence.representation import RetrievalRecord

if TYPE_CHECKING:
    import bm25s

TOKEN_PATTERN = re.compile(r"[^\W_]+(?:[._-][^\W_]+)*", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Preserve product identifiers and version-like tokens."""
    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text)]


class BM25Strategy:
    def __init__(self) -> None:
        self._records: list[RetrievalRecord] = []
        self._retriever: bm25s.BM25 | None = None

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        # BM25S prints its Windows resource-module notice during import. Keep
        # diagnostics on stderr and metadata/JSON commands free of import side effects.
        with redirect_stdout(sys.stderr):
            import bm25s

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
        tokens = tokenize(query)
        scores = self._retriever.get_scores(tokens) if tokens else np.zeros(len(self._records))
        # Score ties use frozen input order rather than backend top-k tie behavior.
        indexes = np.argsort(-scores, kind="stable")[:limit]
        hits = []
        for rank, index in enumerate(indexes, start=1):
            record = self._records[int(index)]
            hits.append(
                RetrievalHit(
                    source_unit_id=record.source.source_unit_id,
                    rank=rank,
                    score=float(scores[int(index)]),
                    evidence_ids=record.source.evidence_ids,
                    preview=record.searchable_text[:240],
                    metadata={"document_id": record.source.document_id},
                )
            )
        return hits
