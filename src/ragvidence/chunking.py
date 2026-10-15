"""Character-bounded child passages with offsets into the unchanged parent."""

import re
from bisect import bisect_right
from typing import Literal


def markdown_sections(text: str) -> list[tuple[int, int, list[str]]]:
    """ATX section offsets and authentic heading paths, excluding fenced code."""
    starts: list[tuple[int, list[str]]] = [(0, [])]
    headings: list[tuple[int, str]] = []
    offset = 0
    fence: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if fence is not None:
            if (
                marker
                and marker[1][0] == fence
                and len(marker[1]) >= fence_length
                and not (line[marker.end() :].strip())
            ):
                fence = None
        elif marker:
            fence, fence_length = marker[1][0], len(marker[1])
        else:
            heading = re.match(r" {0,3}(#{1,6})[ \t]+(.*)", line)
            if heading:
                level = len(heading[1])
                label = re.sub(r"[ \t]+#+[ \t]*$", "", heading[2]).strip()
                headings = [(depth, title) for depth, title in headings if depth < level]
                headings.append((level, label))
                path = [title for _, title in headings]
                if offset == 0:
                    starts[0] = (0, path)
                else:
                    starts.append((offset, path))
        offset += len(line)
    return [
        (start, starts[index + 1][0] if index + 1 < len(starts) else len(text), path)
        for index, (start, path) in enumerate(starts)
    ]


def _recursive_ends(
    text: str, lower: int, upper: int, size: int, separators: tuple[str, ...] = ("\n\n", "\n", " ")
) -> list[int]:
    if upper - lower <= size:
        return [upper]
    if not separators:
        return [*range(lower + size, upper, size), upper]
    separator, *remaining = separators
    ends = []
    start = lower
    position = text.find(separator, start, upper)
    while position != -1:
        end = position + len(separator)
        ends.extend(_recursive_ends(text, start, end, size, tuple(remaining)))
        start = end
        position = text.find(separator, start, upper)
    if start < upper:
        ends.extend(_recursive_ends(text, start, upper, size, tuple(remaining)))
    return ends


def child_spans(
    text: str, *, size: int, overlap: int, splitter: Literal["recursive", "markdown"]
) -> list[tuple[int, int]]:
    """Prefer paragraph, line, then word boundaries; always preserve coverage.

    Markdown mode starts new sections at ATX headings outside fenced code.
    Overlap stays inside each section. Sizes and offsets count characters.
    """
    if size < 1 or not 0 <= overlap < size:
        raise ValueError("Require size > overlap >= 0")
    boundaries = (
        [start for start, _, _ in markdown_sections(text)] if splitter == "markdown" else [0]
    )
    boundaries.append(len(text))
    spans = []
    for lower, upper in zip(boundaries, boundaries[1:], strict=False):
        ends = _recursive_ends(text, lower, upper, size)
        start = lower
        while start < upper:
            end = min(start + size, upper)
            if end < upper:
                index = bisect_right(ends, end) - 1
                if index >= 0 and ends[index] > start + overlap:
                    end = ends[index]
            spans.append((start, end))
            if end == upper:
                break
            start = end - overlap
    return spans
