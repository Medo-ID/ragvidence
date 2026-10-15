"""Offline visible HTML text grouped by heading; no scripts or remote requests."""

import re
from html.parser import HTMLParser

from ragvidence.ingestion.extraction import ExtractedText, Extraction, decode_text

IGNORED = {"script", "style", "head", "template", "noscript"}
BLOCKS = {"p", "div", "section", "article", "li", "br", "tr", "table", "ul", "ol", "pre"}


class _VisibleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.parts: list[str] = []
        self.units: list[ExtractedText] = []
        self.headings: list[tuple[int, str]] = []
        self.heading: tuple[int, list[str]] | None = None

    @property
    def hidden(self) -> bool:
        return any(hidden for _, hidden in self.stack)

    def flush(self) -> None:
        text = re.sub(r"[ \t\r\f\v]+", " ", "".join(self.parts))
        text = re.sub(r" *\n *", "\n", text).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        if text:
            self.units.append(
                ExtractedText(
                    text,
                    {"html_section": len(self.units) + 1},
                    headings=[title for _, title in self.headings],
                )
            )
        self.parts = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        hidden = tag in IGNORED or "hidden" in attributes or attributes.get("aria-hidden") == "true"
        if tag not in {
            "br",
            "hr",
            "img",
            "meta",
            "link",
            "input",
            "wbr",
            "source",
            "embed",
            "area",
            "base",
            "col",
            "param",
            "track",
        }:
            self.stack.append((tag, hidden))
        if self.hidden or hidden:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.flush()
            self.heading = (int(tag[1]), [])
        elif tag in BLOCKS:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if not self.hidden:
            if re.fullmatch(r"h[1-6]", tag) and self.heading is not None:
                level, parts = self.heading
                title = " ".join("".join(parts).split())
                self.headings = [(depth, value) for depth, value in self.headings if depth < level]
                if title:
                    self.headings.append((level, title))
                    self.parts.append(title + "\n")
                self.heading = None
            elif tag in BLOCKS:
                self.parts.append("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            if self.heading is not None:
                self.heading[1].append(data)
            else:
                self.parts.append(data)


def extract_html(raw: bytes) -> Extraction:
    parser = _VisibleHTML()
    parser.feed(decode_text(raw))
    parser.close()
    parser.flush()
    if not parser.units:
        raise ValueError("HTML has no usable visible text")
    return Extraction(
        parser.units,
        "stdlib-html-visible-v1",
        [
            "HTML extraction ignores scripts, styles and hidden attributes; "
            "CSS layout, dynamic content and table relationships are not reconstructed."
        ],
    )
