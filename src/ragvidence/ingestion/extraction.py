"""Small parser contract, independent of discovery, chunking and retrieval."""

from dataclasses import dataclass, field
from typing import Any


class ExtractionLimitError(ValueError):
    """A corpus-wide extraction budget was exceeded; never silently skip it."""


@dataclass(frozen=True)
class ExtractedText:
    text: str
    location: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    headings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Extraction:
    units: list[ExtractedText]
    loader: str
    warnings: list[str] = field(default_factory=list)


def decode_text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Input must be UTF-8 text") from exc
    if not text.strip() or "\x00" in text:
        raise ValueError("Input has no usable text or contains binary data")
    return text
