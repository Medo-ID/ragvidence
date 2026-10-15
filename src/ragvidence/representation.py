"""Controlled searchable representations that never mutate source evidence."""

from dataclasses import dataclass
from typing import Literal

from ragvidence.models import SourceUnit


@dataclass(frozen=True)
class RetrievalRecord:
    source: SourceUnit
    searchable_text: str


def build_records(
    sources: list[SourceUnit], representation: Literal["body", "heading_context", "contextual"]
) -> list[RetrievalRecord]:
    records = []
    for source in sources:
        if representation == "contextual":
            prefix = source.metadata.get("context_prefix")
            if not isinstance(prefix, str) or not prefix.strip():
                raise ValueError(
                    f"{source.source_unit_id}: contextual requires a reviewed "
                    "metadata.context_prefix string on every source"
                )
            text = f"{prefix.strip()}\n\n{source.body}"
        elif representation == "heading_context" and source.heading_path:
            text = f"{' > '.join(source.heading_path)}\n\n{source.body}"
        else:
            text = source.body
        records.append(RetrievalRecord(source=source, searchable_text=text))
    return records
