"""One source of truth for the context inspected, scored and sent to a model."""

from ragvidence.artifacts import content_hash
from ragvidence.models import ContextPassage, RetrievalHit, SourceUnit


def passages_for_hits(
    hits: list[RetrievalHit], sources: dict[str, SourceUnit]
) -> list[ContextPassage]:
    passages = []
    for hit in hits:
        source = sources[hit.source_unit_id]
        start = source.metadata.get("source_start", 0)
        passages.append(
            ContextPassage(
                source_unit_id=source.source_unit_id,
                origin_source_id=source.metadata.get("origin_source_id", source.source_unit_id),
                document_id=source.document_id,
                start=start,
                end=start + len(source.body),
                text=source.body,
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
