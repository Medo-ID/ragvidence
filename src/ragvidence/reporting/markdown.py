"""Human-readable Markdown report derived from authoritative JSON."""

import html
import json
from typing import Any


def _render_evaluation(evaluation: dict[str, Any], heading: str) -> list[str]:
    manifest, summary = evaluation["manifest"], evaluation["summary"]
    config = manifest["config"]
    lines = [
        f"## {heading}: {config['name']}",
        "",
        f"- Strategy: `{config['strategy']}`",
        f"- Representation: `{config['representation']}`",
        f"- Retrieval depth: `k={config['k']}`",
        f"- Dataset hash: `{manifest['dataset_hash']}`",
        f"- Sufficient evidence: **{summary['successful']}/{summary['answerable']}**",
        "",
        "Full retrieval configuration:",
        "",
        "<pre>" + html.escape(json.dumps(config, indent=2)) + "</pre>",
        "",
        *(f"- Run warning: {warning}" for warning in manifest.get("warnings", [])),
        "",
        "## Question results",
        "",
        "| Question | Split | Sufficient | Coverage | First rank |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in evaluation["questions"]:
        sufficient = (
            "N/A" if item["sufficient_evidence"] is None else str(item["sufficient_evidence"])
        )
        coverage = (
            "N/A" if item["evidence_coverage"] is None else f"{item['evidence_coverage']:.2f}"
        )
        rank = item["first_relevant_rank"] if item["first_relevant_rank"] is not None else "N/A"
        lines.append(
            f"| {item['question_id']} | {item['split']} | {sufficient} | {coverage} | {rank} |"
        )
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    if report.get("kind") == "inspection":
        from ragvidence.reporting.inspection import render_inspection_markdown

        return render_inspection_markdown(report)
    lines = ["# RAGvidence report", ""]
    lines.extend(_render_evaluation(report["baseline"], "Baseline"))
    if report.get("intervention") is not None:
        lines.extend([""])
        lines.extend(_render_evaluation(report["intervention"], "Intervention"))
    if report.get("comparison") is not None:
        summary = report["comparison"]["summary"]
        lines.extend(
            [
                "",
                "## Comparison",
                "",
                f"- Improvements: **{summary['fail_to_pass']}**",
                f"- Regressions: **{summary['pass_to_fail']}**",
                f"- Unchanged passes: **{summary['pass_to_pass']}**",
                f"- Unchanged failures: **{summary['fail_to_fail']}**",
            ]
        )
    if report.get("diagnosis") is not None:
        diagnosis = report["diagnosis"]
        lines.extend(
            [
                "",
                "## Diagnosis",
                "",
                f"- Pattern: {diagnosis['pattern']}",
                f"- Evidence: {diagnosis['evidence']}",
                f"- Next experiment: {diagnosis['next_experiment']}",
                f"- Confidence: {diagnosis['confidence']}",
                f"- Limit: {diagnosis['limit']}",
            ]
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"
