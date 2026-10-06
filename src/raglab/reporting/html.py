"""HTML renderer contract. The visual template is owner-contributed."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


def render_html(report: dict[str, Any], template_path: Path) -> str:
    environment = Environment(
        loader=FileSystemLoader(template_path.parent),
        undefined=StrictUndefined,
        autoescape=select_autoescape(default_for_string=True, default=True),
    )
    return environment.get_template(template_path.name).render(report=report)
