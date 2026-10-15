"""Bounded file loading and exact passage materialization for portable inputs."""

import hashlib
from pathlib import Path

from ragvidence.artifacts import content_hash
from ragvidence.chunking import child_spans, markdown_sections
from ragvidence.ingestion.discovery import discover_files
from ragvidence.ingestion.extraction import (
    ExtractedText,
    Extraction,
    ExtractionLimitError,
    decode_text,
)
from ragvidence.ingestion.html import extract_html
from ragvidence.ingestion.models import CorpusSnapshot, InputNotice
from ragvidence.ingestion.pdf import extract_pdf
from ragvidence.ingestion.structured import extract_csv, extract_json
from ragvidence.models import InputPreparation, SourceUnit


def _extract(
    raw: bytes, suffix: str, *, text_field: str | None, max_records: int, max_characters: int
) -> Extraction:
    if suffix in {".json", ".jsonl"}:
        return extract_json(
            raw, jsonl=suffix == ".jsonl", text_field=text_field, max_records=max_records
        )
    if suffix == ".csv":
        return extract_csv(raw, text_field=text_field, max_records=max_records)
    if suffix in {".html", ".htm"}:
        return extract_html(raw)
    if suffix == ".pdf":
        return extract_pdf(raw, max_records=max_records, max_characters=max_characters)
    return Extraction([ExtractedText(decode_text(raw))], "utf8-text-v1")


def _load_file(
    path: Path,
    relative_name: str,
    *,
    max_bytes: int,
    text_field: str | None,
    max_records: int,
    max_characters: int,
) -> tuple[list[SourceUnit], list[InputNotice]]:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes}-byte limit")
    with path.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes}-byte limit")
    extraction = _extract(
        raw,
        path.suffix.lower(),
        text_field=text_field,
        max_records=max_records,
        max_characters=max_characters,
    )
    if len(extraction.units) > max_records:
        raise ValueError(f"Input exceeds the {max_records}-record limit")
    if sum(len(unit.text) for unit in extraction.units) > max_characters:
        raise ExtractionLimitError(f"Input exceeds the {max_characters}-character extraction limit")
    digest = hashlib.sha256(raw).hexdigest()
    documents = []
    for unit in extraction.units:
        document_id = (
            "doc-"
            + content_hash(
                {
                    "path": relative_name,
                    "file_sha256": digest,
                    "loader": extraction.loader,
                    "location": unit.location,
                    "text_hash": content_hash(unit.text),
                }
            )[:20]
        )
        documents.append(
            SourceUnit(
                source_unit_id=document_id,
                document_id=document_id,
                body=unit.text,
                heading_path=unit.headings,
                metadata={
                    "source_path": relative_name,
                    "file_sha256": digest,
                    "text_hash": content_hash(unit.text),
                    "file_bytes": len(raw),
                    "loader": extraction.loader,
                    "format": path.suffix.lower(),
                    "location": unit.location,
                    "record_metadata": unit.metadata,
                },
            )
        )
    notices = [
        InputNotice(path=relative_name, reason=message, kind="warning")
        for message in extraction.warnings
    ]
    return documents, notices


def split_document(document: SourceUnit, *, size: int, overlap: int) -> list[SourceUnit]:
    markdown = document.metadata["format"] in {".md", ".markdown"}
    sections = (
        markdown_sections(document.body)
        if markdown
        else [(0, len(document.body), document.heading_path)]
    )
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
                    "line_end": document.body.count("\n", 0, end - 1) + 1,
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
    text_field: str | None = None,
    max_records: int = 10000,
    max_extracted_characters: int = 20 * 1024 * 1024,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> CorpusSnapshot:
    if not 0 <= overlap < size:
        raise ValueError("Require chunk size > overlap >= 0")
    limits = {
        "max_file_bytes": max_file_bytes,
        "max_total_bytes": max_total_bytes,
        "max_files": max_files,
        "max_records": max_records,
        "max_extracted_characters": max_extracted_characters,
    }
    if any(value < 1 for value in limits.values()):
        raise ValueError("Input limits must be positive")
    files, skipped = discover_files(
        source,
        exclude=exclude,
        max_files=max_files,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )
    root = source if source.is_dir() else source.parent
    documents, passages = [], []
    total_bytes, total_characters = 0, 0
    for path in files:
        relative = path.relative_to(root).as_posix()
        # Count attempted input bytes too, including malformed files in mixed folders.
        try:
            total_bytes += path.stat().st_size
        except OSError as exc:
            if source.is_file():
                raise ValueError(f"Cannot load {relative}: {exc}") from exc
            skipped.append(InputNotice(path=relative, reason=str(exc), kind="failed"))
            continue
        if total_bytes > max_total_bytes:
            raise ValueError(f"Input exceeds the {max_total_bytes}-byte total limit")
        try:
            loaded, notices = _load_file(
                path,
                relative,
                max_bytes=max_file_bytes,
                text_field=text_field,
                max_records=max_records,
                max_characters=max_extracted_characters - total_characters,
            )
        except ExtractionLimitError:
            raise
        except (ValueError, OSError, RecursionError) as exc:
            if source.is_file():
                raise ValueError(f"Cannot load {relative}: {exc}") from exc
            skipped.append(InputNotice(path=relative, reason=str(exc), kind="failed"))
            continue
        total_characters += sum(len(document.body) for document in loaded)
        documents.extend(loaded)
        skipped.extend(notices)
        for document in loaded:
            passages.extend(split_document(document, size=size, overlap=overlap))
    if not documents or not passages:
        reasons = "; ".join(f"{item.path}: {item.reason}" for item in skipped[:5])
        raise ValueError(f"No usable text found in the input. {reasons}")
    return CorpusSnapshot(
        documents=documents,
        passages=passages,
        skipped=skipped,
        preparation=InputPreparation(
            implementation="portable-files-v1",
            chunk_size=size,
            chunk_overlap=overlap,
            text_field=text_field,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
            limits=limits,
        ),
    )
