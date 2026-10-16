"""External results with verified original spans, or explicitly limited ID proxies."""

import json
from pathlib import Path

from pydantic import Field

from ragvidence.artifacts import content_hash
from ragvidence.budgets import ContextCounter, select_context, tokenizer_hash
from ragvidence.context import context_fields
from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import (
    ExperimentRun,
    QueryRun,
    RetrievalHit,
    SearchQuestion,
    SourceUnit,
    StageTrace,
    StrategyConfig,
    StrictModel,
)
from ragvidence.runner import build_manifest


class ImportedHit(StrictModel):
    source_unit_id: str | None = None
    source_id: str | None = None
    start: int | None = Field(default=None, ge=0, strict=True)
    end: int | None = Field(default=None, ge=1, strict=True)
    text: str | None = None
    rank: int | None = Field(default=None, ge=1, strict=True)
    score: float = Field(default=0.0, strict=True)


class ImportedQuery(StrictModel):
    question_id: str
    hits: list[ImportedHit]
    query_time_ms: float | None = Field(default=None, ge=0)


def import_portable(
    path: Path,
    snapshot: CorpusSnapshot,
    questions: list[SearchQuestion],
    config: StrategyConfig,
    *,
    dataset_hash: str,
    references_hash: str | None,
    known_question_ids: set[str] | None = None,
) -> tuple[ExperimentRun, list[SourceUnit], bool]:
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Imported results exceed 50 MiB")
    if config.tokenizer_file:
        config = config.model_copy(update={"tokenizer_hash": tokenizer_hash(config.tokenizer_file)})
    originals = {source.source_unit_id: source for source in snapshot.documents}
    sources = {
        source.source_unit_id: source for source in [*snapshot.documents, *snapshot.passages]
    }
    parsed = [
        ImportedQuery.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = [query.question_id for query in parsed]
    selected_ids = {question.question_id for question in questions}
    if (
        len(ids) != len(set(ids))
        or not selected_ids <= set(ids)
        or set(ids) - (known_question_ids or selected_ids)
    ):
        raise ValueError("Imported results must contain every supplied question exactly once")
    modes, queries = set(), []
    counter = ContextCounter(config.tokenizer_file, config.tokenizer_hash)
    for query in parsed:
        hits, seen = [], set()
        for rank, item in enumerate(query.hits, 1):
            if item.rank is not None and item.rank != rank:
                raise ValueError("Imported ranks must be contiguous from one")
            if item.source_unit_id is not None:
                if any(
                    value is not None for value in (item.source_id, item.start, item.end, item.text)
                ):
                    raise ValueError("Use either an ID-only hit or an exact original span")
                source = sources.get(item.source_unit_id)
                if source is None:
                    raise ValueError("Imported ID-only hit references an unknown source")
                modes.add("id")
            else:
                original = originals.get(item.source_id)
                if original is None or item.start is None or item.end is None or not item.text:
                    raise ValueError("Exact imports require source_id, start, end and text")
                if (
                    item.end - item.start != len(item.text)
                    or original.body[item.start : item.end] != item.text
                ):
                    raise ValueError("Imported context does not match its original source span")
                source_id = (
                    "import-"
                    + content_hash(
                        {"origin": item.source_id, "start": item.start, "end": item.end}
                    )[:20]
                )
                source = SourceUnit(
                    source_unit_id=source_id,
                    document_id=original.document_id,
                    body=item.text,
                    heading_path=original.heading_path,
                    metadata={
                        **original.metadata,
                        "origin_source_id": original.source_unit_id,
                        "source_start": item.start,
                        "source_end": item.end,
                    },
                )
                sources[source_id] = source
                modes.add("exact")
            if source.source_unit_id in seen:
                raise ValueError("Duplicate imported source/span in one ranking")
            seen.add(source.source_unit_id)
            hits.append(
                RetrievalHit(
                    source_unit_id=source.source_unit_id,
                    rank=rank,
                    score=item.score,
                    preview=source.body[:240],
                )
            )
        # Validate every hit, including tails outside k, before applying the selection policy.
        selected, measurement = select_context(
            hits, sources, k=config.k, budget=config.context_budget, counter=counter
        )
        queries.append(
            QueryRun(
                question_id=query.question_id,
                hits=selected,
                query_time_ms=query.query_time_ms,
                context_measurement=measurement,
                stages=[
                    StageTrace(name="external_results", hits=hits),
                    StageTrace(name="context_selection", hits=selected, details=measurement),
                ],
                **context_fields(selected, sources),
            )
        )
    if len(modes) > 1:
        raise ValueError("Do not mix exact context and ID-only proxies in one imported run")
    proxy = modes == {"id"}
    warnings = ["External stage traces and indexing time are unavailable."]
    if proxy:
        warnings.append(
            "ID-only results describe registered source units, not verified external context. "
            "Span scores are registered-unit proxies and cannot establish actual context quality."
        )
    manifest = build_manifest(
        list(sources.values()),
        questions,
        config,
        dataset_hash=dataset_hash,
        corpus_hash=snapshot.corpus_hash,
        references_hash=references_hash,
        evaluation_level="reviewed_evaluation" if references_hash else "retrieval_inspection",
        input_preparation=snapshot.preparation,
        warnings=warnings,
    )
    return (
        ExperimentRun(
            manifest=manifest,
            queries=[query for query in queries if query.question_id in selected_ids],
        ),
        list(sources.values()),
        proxy,
    )
