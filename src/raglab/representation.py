"""Controlled searchable representations that never mutate source evidence."""

from dataclasses import dataclass
from typing import Literal

from raglab.models import SourceUnit


@dataclass(frozen=True)
class RetrievalRecord:
    source: SourceUnit
    searchable_text: str


def build_records(
    sources: list[SourceUnit], representation: Literal["body", "heading_context"]
) -> list[RetrievalRecord]:
    records = []
    for source in sources:
        if representation == "heading_context" and source.heading_path:
            text = f"{' > '.join(source.heading_path)}\n\n{source.body}"
        else:
            text = source.body
        records.append(RetrievalRecord(source=source, searchable_text=text))
    return records
