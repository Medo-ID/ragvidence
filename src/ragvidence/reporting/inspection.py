"""Compute an unscored diagnostic report once for all presentation formats."""

import html
import json
from datetime import UTC, datetime
from typing import Any

from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import ExperimentRun, SearchQuestion


def source_location(metadata: dict[str, Any]) -> str:
    """Human location in the file; character/line offsets refer to extracted text."""
    location = metadata.get("location", {})
    parts = []
    for field, label in (
        ("page", "Page"),
        ("record", "Record"),
        ("row", "Row"),
        ("html_section", "HTML section"),
        ("file_line", "File line"),
    ):
        if field in location:
            parts.append(f"{label} {location[field]}")
    if "file_line_start" in location:
        parts.append(f"File lines {location['file_line_start']}–{location['file_line_end']}")
    if "text_field" in location:
        parts.append(f"Field {location['text_field']}")
    return " · ".join(parts) or "Source text"


def build_inspection_report(
    snapshot: CorpusSnapshot,
    questions: list[SearchQuestion],
    run: ExperimentRun,
    *,
    name: str,
    evaluation: dict | None = None,
) -> dict[str, Any]:
    by_id = {question.question_id: question for question in questions}
    originals = {source.source_unit_id: source for source in snapshot.documents}
    metrics = {row["question_id"]: row for row in evaluation["questions"]} if evaluation else {}
    results = []
    for query in run.queries:
        hits = []
        for hit, context in zip(query.hits, query.context, strict=True):
            source = originals[context.origin_source_id]
            hits.append(
                {
                    **hit.model_dump(mode="json"),
                    "text": context.text,
                    "heading_path": context.heading_path,
                    "source_path": source.metadata["source_path"],
                    "location": source.metadata.get("location", {}),
                    "location_label": source_location(source.metadata),
                    "loader": source.metadata["loader"],
                    "start": context.start,
                    "end": context.end,
                    "origin_source_id": context.origin_source_id,
                    "line_start": source.body.count("\n", 0, context.start) + 1,
                    "line_end": source.body.count("\n", 0, context.end - 1) + 1,
                }
            )
        observations = []
        if not hits:
            observations.append("No passages were returned.")
        elif (
            run.manifest.config.strategy == "bm25"
            and not run.manifest.config.reranker_model
            and not run.manifest.config.query_variants
            and not any(hit["score"] > 0 for hit in hits)
        ):
            observations.append(
                "All returned BM25 scores are zero: the query has no positive lexical match."
            )
        results.append(
            {
                "question_id": query.question_id,
                "question": by_id[query.question_id].question,
                "hits": hits,
                "query_time_ms": query.query_time_ms,
                "context_characters": query.returned_context_characters,
                "context_hash": query.context_hash,
                "observations": observations,
                "metrics": metrics.get(query.question_id),
                "context_measurement": query.context_measurement,
                "stages": [stage.model_dump(mode="json") for stage in query.stages],
            }
        )
    source_only = run.manifest.evaluation_level == "ingestion_only"
    return {
        "schema_version": 1,
        "kind": "inspection",
        "generated_at": datetime.now(UTC).isoformat(),
        "evaluation_level": run.manifest.evaluation_level,
        "preparation": snapshot.preparation.model_dump(mode="json"),
        "manifest": run.manifest.model_dump(mode="json"),
        "evaluation": evaluation,
        "input": {
            "name": name,
            "corpus_hash": snapshot.corpus_hash,
            "document_count": len(snapshot.documents),
            "file_count": len({source.metadata["source_path"] for source in snapshot.documents}),
            "passage_count": len(snapshot.passages),
            "source_characters": sum(len(source.body) for source in snapshot.documents),
            "indexed_characters": sum(len(source.body) for source in snapshot.passages),
            "skipped": [notice.model_dump() for notice in snapshot.skipped],
            "skipped_count": sum(notice.kind == "skipped" for notice in snapshot.skipped),
            "failed_count": sum(notice.kind == "failed" for notice in snapshot.skipped),
            "warning_count": sum(notice.kind == "warning" for notice in snapshot.skipped),
            "sources": [
                {
                    "source_unit_id": source.source_unit_id,
                    "source_path": source.metadata["source_path"],
                    "location": source.metadata.get("location", {}),
                    "location_label": source_location(source.metadata),
                    "heading_path": source.heading_path,
                    "loader": source.metadata["loader"],
                    "file_sha256": source.metadata["file_sha256"],
                    "text_hash": source.metadata["text_hash"],
                    "characters": len(source.body),
                }
                for source in snapshot.documents
            ],
        },
        "questions": results,
        "observations": (
            ["Retrieval was not executed because no questions were supplied."]
            if source_only
            else ["Reviewed evidence is scored against the union of exact original-text spans."]
            if evaluation
            else ["Ranked passages are shown for inspection; relevance has not been scored."]
        )
        + run.manifest.warnings,
        "limitations": [
            *(
                []
                if evaluation
                else [
                    "No reviewed expected evidence was supplied. Evidence sufficiency "
                    "and recall are not scored."
                ]
            ),
            "Answer correctness, citations, abstention and generation request tokens "
            "are not evaluated.",
            "Retriever scores describe this ranking; they are not probabilities of correctness.",
            "Chunk sizes count characters. Rendered context counts characters unless an "
            "explicit local tokenizer is identified; model request overhead is excluded.",
            "Character and text-line offsets refer to the extracted page/record/section, "
            "not byte offsets in the original file. Extraction does not verify layout fidelity.",
        ],
    }


def render_inspection_markdown(report: dict[str, Any]) -> str:
    def escape(value: Any) -> str:
        return html.escape("N/A" if value is None else str(value))

    info = report["input"]
    lines = [
        "# RAGvidence diagnostic report",
        "",
        f"Status: **{report['evaluation_level']}**",
        "",
        f"Input: {escape(info['name'])}",
        "",
        f"Sources: {info['document_count']} · Passages: {info['passage_count']}",
        "",
        f"Passage size: {report['preparation']['chunk_size']} characters; "
        f"overlap: {report['preparation']['chunk_overlap']} characters.",
        "",
        f"Corpus hash: `{info['corpus_hash']}`",
        "",
    ]
    lines.extend(f"- {escape(observation)}" for observation in report["observations"])
    if report["evaluation"]:
        evaluation = report["evaluation"]
        lines.extend(
            [
                "",
                "## Reviewed evidence",
                "",
                f"Scope: {escape(evaluation['scope'])} · Method: {escape(evaluation['method'])}",
                "",
            ]
        )
        for split, summary in evaluation["summaries"].items():
            lines.append(
                f"- {split}: {summary['sufficient_count']} / {summary['answerable_questions']} "
                f"answerable questions sufficient · Rate: {escape(summary['sufficiency_rate'])}"
            )
    for question in report["questions"]:
        lines.extend(
            [
                "",
                f"## {escape(question['question'])}",
                "",
                f"Context characters: {question['context_characters']}",
                "",
            ]
        )
        lines.extend(f"- {escape(observation)}" for observation in question["observations"])
        if question["metrics"]:
            row = question["metrics"]
            lines.extend(
                [
                    "",
                    f"Sufficient evidence: {escape(row['sufficient_evidence'])} · "
                    f"Evidence coverage: {escape(row['evidence_coverage'])}",
                    f"Missing evidence: {escape(', '.join(row['missing_evidence_ids']))}",
                ]
            )
        measurement = question["context_measurement"]
        if measurement:
            budget = measurement["budget"] if measurement["budget"] is not None else "unlimited"
            lines.extend(
                [
                    "",
                    f"Rendered context: {measurement['count']} {measurement['unit']} · "
                    f"Budget: {budget}",
                ]
            )
        for hit in question["hits"]:
            lines.extend(
                [
                    "",
                    f"### Rank {hit['rank']} · {escape(hit['source_path'])}",
                    "",
                    f"Score: {hit['score']:.6f} · {escape(hit['location_label'])} · "
                    f"Extracted lines {hit['line_start']}–{hit['line_end']}",
                    "",
                    "<pre>" + escape(hit["text"]) + "</pre>",
                ]
            )
        if question["stages"]:
            lines.extend(
                [
                    "",
                    "<details><summary>Stage evidence</summary><pre>"
                    + escape(json.dumps(question["stages"], ensure_ascii=False, indent=2))
                    + "</pre></details>",
                ]
            )
    lines.extend(["", "## Extracted sources", ""])
    lines.extend(
        f"- {escape(item['source_path'])}: {escape(item['location_label'])} · "
        f"{escape(item['loader'])} · {item['characters']} characters · "
        f"ID: {escape(item['source_unit_id'])} · Text hash: {escape(item['text_hash'])}"
        for item in info["sources"]
    )
    if info["skipped"]:
        lines.extend(["", "## Input notices", ""])
        lines.extend(
            f"- {escape(item['kind'])} · {escape(item['path'])}: {escape(item['reason'])}"
            for item in info["skipped"]
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {escape(item)}" for item in report["limitations"])
    return "\n".join(lines) + "\n"
