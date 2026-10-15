"""Compute an unscored diagnostic report once for all presentation formats."""

import html
from datetime import UTC, datetime
from typing import Any

from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import ExperimentRun, SearchQuestion


def build_inspection_report(
    snapshot: CorpusSnapshot, questions: list[SearchQuestion], run: ExperimentRun, *, name: str
) -> dict[str, Any]:
    by_id = {question.question_id: question for question in questions}
    passages = {source.source_unit_id: source for source in snapshot.passages}
    results = []
    for query in run.queries:
        hits = []
        for hit, context in zip(query.hits, query.context, strict=True):
            source = passages[hit.source_unit_id]
            hits.append(
                {
                    **hit.model_dump(mode="json"),
                    "text": context.text,
                    "heading_path": context.heading_path,
                    "source_path": source.metadata["source_path"],
                    "start": context.start,
                    "end": context.end,
                    "line_start": source.metadata["line_start"],
                    "line_end": source.metadata["line_end"],
                }
            )
        observations = []
        if not hits:
            observations.append("No passages were returned.")
        elif run.manifest.config.strategy == "bm25" and not any(hit["score"] > 0 for hit in hits):
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
        "input": {
            "name": name,
            "corpus_hash": snapshot.corpus_hash,
            "document_count": len(snapshot.documents),
            "passage_count": len(snapshot.passages),
            "source_characters": sum(len(source.body) for source in snapshot.documents),
            "indexed_characters": sum(len(source.body) for source in snapshot.passages),
            "skipped": [notice.model_dump() for notice in snapshot.skipped],
        },
        "questions": results,
        "observations": (
            ["Retrieval was not executed because no questions were supplied."]
            if source_only
            else ["Ranked passages are shown for inspection; relevance has not been scored."]
        ),
        "limitations": [
            "No reviewed expected evidence was supplied. Evidence sufficiency, recall and "
            "answer correctness are not scored.",
            "Retriever scores describe this ranking; they are not probabilities of correctness.",
            "Chunk sizes and context measurements count characters, not model tokens.",
        ],
    }


def render_inspection_markdown(report: dict[str, Any]) -> str:
    def escape(value: Any) -> str:
        return html.escape(str(value))

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
        for hit in question["hits"]:
            lines.extend(
                [
                    "",
                    f"### Rank {hit['rank']} · {escape(hit['source_path'])}",
                    "",
                    f"Score: {hit['score']:.6f} · Lines {hit['line_start']}–{hit['line_end']}",
                    "",
                    "<pre>" + escape(hit["text"]) + "</pre>",
                ]
            )
    if info["skipped"]:
        lines.extend(["", "## Skipped inputs", ""])
        lines.extend(
            f"- {escape(item['path'])}: {escape(item['reason'])}" for item in info["skipped"]
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {escape(item)}" for item in report["limitations"])
    return "\n".join(lines) + "\n"
