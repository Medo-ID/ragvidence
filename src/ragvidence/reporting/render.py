"""Shared format dispatch for graded and unscored reports."""

import json
from pathlib import Path
from typing import Any

from ragvidence.reporting.html import render_html
from ragvidence.reporting.markdown import render_markdown


def render_report(report: dict[str, Any], format: str) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if format == "markdown":
        return render_markdown(report)
    if format == "html":
        name = "inspection" if report.get("kind") == "inspection" else "report"
        return render_html(report, Path(__file__).parent / "templates" / f"{name}.html.j2")
    raise ValueError("format must be html, json or markdown")
