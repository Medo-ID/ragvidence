"""Search small children, return full parents with their reviewed evidence."""

import time
from collections.abc import Sequence
from typing import Literal

from ragvidence.chunking import child_spans
from ragvidence.models import RetrievalHit, SourceUnit, StageTrace
from ragvidence.representation import RetrievalRecord
from ragvidence.strategies.base import RetrievalStrategy


class ParentChildStrategy:
    def __init__(
        self,
        child_strategy: RetrievalStrategy,
        *,
        splitter: Literal["recursive", "markdown"],
        size: int,
        overlap: int,
        candidate_k: int,
        fixed_depth: bool = False,
    ) -> None:
        self.child_strategy = child_strategy
        self.splitter, self.size, self.overlap = splitter, size, overlap
        self.candidate_k = candidate_k
        self.fixed_depth = fixed_depth
        self.last_trace: list[StageTrace] = []
        self._parents: dict[str, tuple[SourceUnit, int, int]] = {}

    def index(self, records: Sequence[RetrievalRecord]) -> None:
        self._parents = {}
        children = []
        for record in records:
            source = record.source
            prefix = record.searchable_text[: -len(source.body)]
            for start, end in child_spans(
                source.body, size=self.size, overlap=self.overlap, splitter=self.splitter
            ):
                child_id = f"child-{len(children)}"
                child = SourceUnit(
                    source_unit_id=child_id,
                    document_id=source.document_id,
                    body=source.body[start:end],
                )
                children.append(RetrievalRecord(child, prefix + child.body))
                self._parents[child_id] = (source, start, end)
        self.child_strategy.index(children)

    def search(self, query: str, *, k: int) -> list[RetrievalHit]:
        depth = self.candidate_k if self.fixed_depth else max(k, self.candidate_k)
        started = time.perf_counter()
        children = self.child_strategy.search(query, k=depth)
        self.last_trace = list(getattr(self.child_strategy, "last_trace", []))
        self.last_trace.append(
            StageTrace(
                name="children",
                elapsed_ms=(time.perf_counter() - started) * 1000,
                hits=children,
                details={
                    "query": query,
                    "limit": depth,
                    "locations": [
                        {
                            "child_id": hit.source_unit_id,
                            "parent_id": self._parents[hit.source_unit_id][0].source_unit_id,
                            "start": self._parents[hit.source_unit_id][1],
                            "end": self._parents[hit.source_unit_id][2],
                        }
                        for hit in children
                    ],
                },
            )
        )
        started = time.perf_counter()
        seen = set()
        parents = []
        for hit in children:
            source, start, end = self._parents[hit.source_unit_id]
            if source.source_unit_id in seen:
                continue
            seen.add(source.source_unit_id)
            parents.append(
                RetrievalHit(
                    source_unit_id=source.source_unit_id,
                    rank=len(parents) + 1,
                    score=hit.score,
                    evidence_ids=source.evidence_ids,
                    preview=source.body[:240],
                    metadata={
                        **hit.metadata,
                        "document_id": source.document_id,
                        "matched_child_id": hit.source_unit_id,
                        "matched_child_start": start,
                        "matched_child_end": end,
                        "returned_context": "full_parent",
                    },
                )
            )
            if len(parents) == k:
                break
        self.last_trace.append(
            StageTrace(
                name="parent_expansion",
                hits=parents,
                elapsed_ms=(time.perf_counter() - started) * 1000,
                details={"query": query},
            )
        )
        return parents
