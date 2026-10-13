"""Render the self-contained, shareable HTML diagnostic report."""

from base64 import b64encode
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


@lru_cache(maxsize=1)
def _embedded_fonts() -> dict[str, str]:
    root = Path(__file__).parent / "fonts"
    return {
        "sans": b64encode((root / "Geist-Sans.woff2").read_bytes()).decode("ascii"),
        "mono": b64encode((root / "Geist-Mono.woff2").read_bytes()).decode("ascii"),
        "license": (root / "LICENSE.txt").read_text(encoding="utf-8"),
    }


def render_html(report: dict[str, Any], template_path: Path) -> str:
    environment = Environment(
        loader=FileSystemLoader(template_path.parent),
        undefined=StrictUndefined,
        autoescape=select_autoescape(default_for_string=True, default=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return environment.get_template(template_path.name).render(
        report=report, fonts=_embedded_fonts()
    )
