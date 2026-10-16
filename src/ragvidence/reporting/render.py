"""Shared format dispatch for graded and unscored reports."""

import json
from pathlib import Path
from typing import Any

from ragvidence.reporting.comparison import render_comparison_markdown
from ragvidence.reporting.html import render_html
from ragvidence.reporting.markdown import render_markdown


def render_report(report: dict[str, Any], format: str) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if format == "markdown":
        if report.get("kind") == "comparison":
            return render_comparison_markdown(report)
        return render_markdown(report)
    if format == "html":
        name = report["kind"] if report.get("kind") in {"inspection", "comparison"} else "report"
        return render_html(report, Path(__file__).parent / "templates" / f"{name}.html.j2")
    raise ValueError("format must be html, json or markdown")
