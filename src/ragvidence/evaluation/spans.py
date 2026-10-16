"""Evidence credit from the union of actual returned original-text intervals."""

from collections import defaultdict

from ragvidence.evaluation.aggregation import summarize
from ragvidence.models import ContextPassage, ExperimentRun
from ragvidence.reviewed import EvidenceItem, ReviewedReferences


def merged_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def completed_evidence(items: list[EvidenceItem], context: list[ContextPassage]) -> set[str]:
    ranges = defaultdict(list)
    for passage in context:
        ranges[passage.origin_source_id].append((passage.start, passage.end))
    ranges = {source: merged_intervals(intervals) for source, intervals in ranges.items()}
    return {
        item.evidence_id
        for item in items
        if all(
            any(
                start <= span.start and end >= span.end
                for start, end in ranges.get(span.source_id, [])
            )
            for span in item.spans
        )
    }


def score_spans(run: ExperimentRun, references: ReviewedReferences) -> dict:
    """Caller must validate corpus, references and run provenance before scoring."""
    by_id = {query.question_id: query for query in run.queries}
    results = []
    for question in references.questions:
        query = by_id[question.question_id]
        required = question.required_evidence_ids
        required_items = [item for item in references.evidence if item.evidence_id in required]
        complete = completed_evidence(required_items, query.context)
        found = sorted(required & complete)
        missing = sorted(required - complete)
        first_rank = next(
            (
                rank
                for rank in range(1, len(query.hits) + 1)
                if required
                & completed_evidence(
                    required_items,
                    [
                        p
                        for p in query.context
                        if p.source_unit_id in {hit.source_unit_id for hit in query.hits[:rank]}
                    ],
                )
            ),
            None,
        )
        relevant = sum(
            any(
                span.source_id == passage.origin_source_id
                and max(span.start, passage.start) < min(span.end, passage.end)
                for item in required_items
                for span in item.spans
                for passage in query.context
                if passage.source_unit_id == hit.source_unit_id
            )
            for hit in query.hits
        )
        results.append(
            {
                "question_id": question.question_id,
                "split": question.split,
                "answerable": question.answerable,
                "tags": sorted(question.tags),
                "required_evidence_ids": sorted(required),
                "found_evidence_ids": found,
                "missing_evidence_ids": missing,
                "sufficient_evidence": not missing if required else None,
                "evidence_coverage": len(found) / len(required) if required else None,
                "first_complete_evidence_rank": first_rank,
                "reciprocal_rank": (1 / first_rank if first_rank else 0.0) if required else None,
                "precision_at_k": relevant / run.manifest.config.k if required else None,
            }
        )
    summaries = {
        split: summarize([row for row in results if row["split"] == split])
        for split in ("dev", "heldout")
    }
    return {
        "schema_version": 1,
        "method": "original-span-union-v1",
        "references_hash": references.identity,
        "questions": results,
        "summaries": summaries,
        "definitions": {
            "reciprocal_rank": "First rank prefix completing at least one required evidence item",
            "precision_at_k": "Returned hits overlapping required spans divided by configured k",
            "sufficiency": "All spans of every required item covered by the returned union",
            "unanswerable": "Excluded from retrieval quality rates; abstention is not evaluated",
        },
    }
