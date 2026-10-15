"""Portable input snapshots, separate from optional evaluation labels."""

from typing import Literal

from ragvidence.artifacts import content_hash
from ragvidence.models import InputPreparation, SourceUnit, StrictModel


class InputNotice(StrictModel):
    path: str
    reason: str
    kind: Literal["skipped", "failed", "warning"] = "skipped"


class CorpusSnapshot(StrictModel):
    schema_version: Literal[1] = 1
    documents: list[SourceUnit]
    passages: list[SourceUnit]
    skipped: list[InputNotice]
    preparation: InputPreparation

    @property
    def corpus_hash(self) -> str:
        return content_hash(self.documents)
