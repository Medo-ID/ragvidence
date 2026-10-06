"""Common retrieval strategy protocol."""

from collections.abc import Sequence
from typing import Protocol

from raglab.models import RetrievalHit
from raglab.representation import RetrievalRecord


class RetrievalStrategy(Protocol):
    def index(self, records: Sequence[RetrievalRecord]) -> None: ...
    def search(self, query: str, *, k: int) -> list[RetrievalHit]: ...
