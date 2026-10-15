"""Text loading and exact passage materialization for portable inputs."""

import hashlib
from pathlib import Path

from ragvidence.artifacts import content_hash
from ragvidence.chunking import child_spans, markdown_sections
from ragvidence.ingestion.discovery import discover_files
from ragvidence.ingestion.models import CorpusSnapshot, InputNotice
from ragvidence.models import InputPreparation, SourceUnit


def _load_text(path: Path, relative_name: str, max_bytes: int) -> SourceUnit:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes}-byte limit")
    with path.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes}-byte limit")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Input must be UTF-8 text") from exc
    if not text.strip() or "\x00" in text:
        raise ValueError("Input has no usable text or contains binary data")
    digest = hashlib.sha256(raw).hexdigest()
    document_id = "doc-" + content_hash({"path": relative_name, "file_sha256": digest})[:20]
    return SourceUnit(
        source_unit_id=document_id,
        document_id=document_id,
        body=text,
        metadata={
            "source_path": relative_name,
            "file_sha256": digest,
            "text_hash": content_hash(text),
            "file_bytes": len(raw),
            "loader": "utf8-text-v1",
            "format": path.suffix.lower(),
        },
    )


def split_document(document: SourceUnit, *, size: int, overlap: int) -> list[SourceUnit]:
    markdown = document.metadata["format"] in {".md", ".markdown"}
    sections = markdown_sections(document.body) if markdown else [(0, len(document.body), [])]
    spans = child_spans(
        document.body, size=size, overlap=overlap, splitter="markdown" if markdown else "recursive"
    )
    passages = []
    for start, end in spans:
        body = document.body[start:end]
        if not body.strip():
            continue
        headings = next((path for lower, upper, path in sections if lower <= start < upper), [])
        identity = {
            "source": document.source_unit_id,
            "start": start,
            "end": end,
            "splitter": "markdown-v1" if markdown else "recursive-v1",
            "size": size,
            "overlap": overlap,
        }
        passages.append(
            SourceUnit(
                source_unit_id="passage-" + content_hash(identity)[:20],
                document_id=document.document_id,
                body=body,
                heading_path=headings,
                metadata={
                    **document.metadata,
                    "origin_source_id": document.source_unit_id,
                    "source_start": start,
                    "source_end": end,
                    "line_start": document.body.count("\n", 0, start) + 1,
                    "line_end": document.body.count("\n", 0, end) + 1,
                },
            )
        )
    return passages


def load_corpus(
    source: Path,
    *,
    exclude: list[Path],
    size: int = 500,
    overlap: int = 50,
    max_file_bytes: int = 20 * 1024 * 1024,
    max_total_bytes: int = 100 * 1024 * 1024,
    max_files: int = 1000,
) -> CorpusSnapshot:
    if not 0 <= overlap < size:
        raise ValueError("Require chunk size > overlap >= 0")
    files, skipped = discover_files(source, exclude=exclude, max_files=max_files)
    root = source if source.is_dir() else source.parent
    documents = []
    passages = []
    total_bytes = 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            document = _load_text(path, relative, max_file_bytes)
        except (ValueError, OSError) as exc:
            if source.is_file():
                raise ValueError(f"Cannot load {relative}: {exc}") from exc
            skipped.append(InputNotice(path=relative, reason=str(exc)))
            continue
        total_bytes += document.metadata["file_bytes"]
        if total_bytes > max_total_bytes:
            raise ValueError(f"Input exceeds the {max_total_bytes}-byte total limit")
        documents.append(document)
        passages.extend(split_document(document, size=size, overlap=overlap))
    if not documents or not passages:
        raise ValueError("No usable TXT/Markdown text found in the input")
    return CorpusSnapshot(
        documents=documents,
        passages=passages,
        skipped=skipped,
        preparation=InputPreparation(chunk_size=size, chunk_overlap=overlap),
    )
