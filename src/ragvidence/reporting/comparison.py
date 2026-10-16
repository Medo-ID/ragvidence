"""Markdown presentation for precomputed portable comparison facts."""

import html
import json


def render_comparison_markdown(report: dict) -> str:
    def escape(value):
        return html.escape("N/A" if value is None else str(value))

    lines = [
        "# RAGvidence technique comparison",
        "",
        f"Input: {escape(report['input_name'])}",
        "",
        f"Status: {report['state']} · Policy: {report['policy']} · Phase: {report['phase']}",
        "",
        f"Baseline: {escape(report['baseline'])}",
        "",
    ]
    lines.extend(f"- {escape(value)}" for value in report["observations"])
    for entry in report["participants"]:
        lines.extend(["", f"## {escape(entry['name'])}", "", f"Status: {entry['state']}", ""])
        if entry["state"] != "complete":
            lines.append(escape(entry["error"]))
            continue
        lines.extend([f"Evidence scope: {entry['evidence_scope']}", ""])
        lines.extend(f"- {escape(value)}" for value in entry["report"]["observations"])
        for split, scopes in entry["summaries"].items():
            for name, summary in scopes.items():
                lines.append(
                    f"{split}/{escape(name)}: {summary['sufficient_count']} / "
                    f"{summary['answerable_questions']} answerable sufficient · "
                    f"Coverage: {escape(summary['mean_evidence_coverage'])} · "
                    f"MRR: {escape(summary['mean_reciprocal_rank'])} · "
                    f"Precision: {escape(summary['mean_precision_at_k'])}"
                )
        measurement = entry["resources"]
        lines.extend(
            [
                "",
                f"Mean known query ms: {escape(measurement['query_ms']['mean_known'])} "
                f"({measurement['query_ms']['missing_count']} missing)",
                f"Mean context: {escape(measurement['context_units']['mean_known'])} "
                f"{escape(measurement['context_unit'])}",
                f"Estimated supplied-usage cost: {escape(entry['usage']['cost'])} "
                f"{escape(entry['usage']['currency'])}",
            ]
        )
        for question in entry["report"]["questions"]:
            lines.extend(["", f"### {escape(question['question'])}", ""])
            for hit in question["hits"]:
                lines.extend(
                    [
                        f"Rank {hit['rank']} · {escape(hit['source_path'])} · "
                        f"{escape(hit['location_label'])}",
                        "",
                        "<pre>" + escape(hit["text"]) + "</pre>",
                        "",
                    ]
                )
    for pair in report["comparisons"]:
        lines.extend(
            [
                "",
                f"## {escape(pair['participant'])} versus {escape(pair['baseline'])}",
                "",
                escape(pair["interpretation"]),
                "",
                "<pre>"
                + escape(
                    json.dumps({"splits": pair["splits"], "questions": pair["questions"]}, indent=2)
                )
                + "</pre>",
            ]
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {escape(value)}" for value in report["limitations"])
    return "\n".join(lines) + "\n"
