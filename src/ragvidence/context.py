"""One source of truth for the context inspected, scored and sent to a model."""

from ragvidence.artifacts import content_hash
from ragvidence.models import ContextPassage, RetrievalHit, SourceUnit, TextSpan


def passages_for_hits(
    hits: list[RetrievalHit], sources: dict[str, SourceUnit]
) -> list[ContextPassage]:
    passages = []
    for hit in hits:
        source = sources[hit.source_unit_id]
        origin_start = source.metadata.get("source_start", 0)
        spans = hit.context_spans
        if spans is None:
            spans = [TextSpan(start=0, end=len(source.body))]
        previous = 0
        for span in spans:
            if span.start < previous or span.end > len(source.body):
                raise ValueError(
                    "Returned context spans must be ordered, disjoint and within source"
                )
            previous = span.end
            passages.append(
                ContextPassage(
                    source_unit_id=source.source_unit_id,
                    origin_source_id=source.metadata.get("origin_source_id", source.source_unit_id),
                    document_id=source.document_id,
                    start=origin_start + span.start,
                    end=origin_start + span.end,
                    text=source.body[span.start : span.end],
                    heading_path=source.heading_path,
                )
            )
    return passages


def render_context(passages: list[ContextPassage]) -> str:
    return "\n\n".join(
        f"[{passage.source_unit_id}] {' > '.join(passage.heading_path)}\n{passage.text}"
        for passage in passages
    )


def context_fields(hits: list[RetrievalHit], sources: dict[str, SourceUnit]) -> dict:
    passages = passages_for_hits(hits, sources)
    rendered = render_context(passages)
    return {
        "context": passages,
        "rendered_context": rendered,
        "context_hash": content_hash(rendered),
        "returned_context_characters": sum(len(passage.text) for passage in passages),
    }
