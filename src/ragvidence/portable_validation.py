"""Validate exact portable context against frozen originals before span scoring."""

from collections import Counter

from ragvidence.artifacts import content_hash
from ragvidence.budgets import ContextCounter
from ragvidence.context import context_fields, render_context
from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import ExperimentRun, SearchQuestion, SourceUnit
from ragvidence.provenance import configuration_identity, question_identity, representation_identity


def validate_portable_run(
    snapshot: CorpusSnapshot,
    questions: list[SearchQuestion],
    run: ExperimentRun,
    references_hash: str | None = None,
    sources: list[SourceUnit] | None = None,
) -> None:
    run = ExperimentRun.model_validate(run.model_dump())
    manifest = run.manifest
    expected = {
        "dataset_hash": content_hash({"sources": snapshot.passages, "questions": questions}),
        "corpus_hash": snapshot.corpus_hash,
        "questions_hash": question_identity(questions),
        "references_hash": references_hash,
        "configuration_hash": configuration_identity(manifest.config, snapshot.preparation),
    }
    if sources is not None and manifest.config.strategy != "imported":
        expected["representation_hash"] = representation_identity(sources, manifest.config)
    if manifest.input_preparation != snapshot.preparation:
        raise ValueError("Portable input preparation does not match snapshot")
    for key, value in expected.items():
        if getattr(manifest, key) != value:
            raise ValueError(f"Portable run {key} does not match its declared inputs")
    counts = Counter(query.question_id for query in run.queries)
    if set(counts) != {question.question_id for question in questions} or any(
        count != 1 for count in counts.values()
    ):
        raise ValueError("Portable run must contain each question exactly once")
    originals = {source.source_unit_id: source for source in snapshot.documents}
    source_by_id = (
        {source.source_unit_id: source for source in sources} if sources is not None else None
    )
    counter = ContextCounter(manifest.config.tokenizer_file, manifest.config.tokenizer_hash)
    for query in run.queries:
        if source_by_id is not None:
            if any(hit.source_unit_id not in source_by_id for hit in query.hits):
                raise ValueError("Portable hit references an unknown source")
            for key, value in context_fields(query.hits, source_by_id).items():
                if getattr(query, key) != value:
                    raise ValueError(f"Portable {key} does not match declared retrieval sources")
        if len(query.hits) != len(query.context) or len(query.hits) > manifest.config.k:
            raise ValueError("Portable hit/context count does not match retrieval depth")
        seen = set()
        for rank, (hit, context) in enumerate(zip(query.hits, query.context, strict=True), 1):
            if (
                hit.rank != rank
                or hit.source_unit_id != context.source_unit_id
                or hit.source_unit_id in seen
            ):
                raise ValueError("Portable ranks, context IDs or duplicates are invalid")
            seen.add(hit.source_unit_id)
            source = originals.get(context.origin_source_id)
            if (
                source is None
                or source.body[context.start : context.end] != context.text
                or source.document_id != context.document_id
            ):
                raise ValueError("Portable context does not match original source spans")
            if hit.evidence_ids:
                raise ValueError("Portable evidence credit must come from reviewed span unions")
        rendered = render_context(query.context)
        if query.rendered_context != rendered or query.context_hash != content_hash(rendered):
            raise ValueError("Portable rendered context/hash does not match returned text")
        if query.returned_context_characters != sum(len(passage.text) for passage in query.context):
            raise ValueError("Portable context character count does not match")
        if query.context_measurement:
            measurement = query.context_measurement
            expected_count = counter.count(rendered)
            if measurement.get("count") != expected_count or any(
                measurement.get(key) != value for key, value in counter.identity.items()
            ):
                raise ValueError(
                    "Portable context measurement does not match its identified counter"
                )
            if (
                manifest.config.context_budget is not None
                and expected_count > manifest.config.context_budget
            ):
                raise ValueError("Portable context exceeds the declared budget")
