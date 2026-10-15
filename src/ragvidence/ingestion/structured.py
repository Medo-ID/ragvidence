"""Document records: one explicit text value, never flattened evaluation labels."""

import csv
import io
import json
from typing import Any

from ragvidence.ingestion.extraction import ExtractedText, Extraction, decode_text

TEXT_FIELDS = {"text", "content", "body"}
RESERVED_FIELDS = {
    "question",
    "question_id",
    "reference_answer",
    "answer",
    "expected_answer",
    "evidence_ids",
    "source_unit_id",
    "manifest",
    "queries",
    "evaluation_level",
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON value: {value}")


def _json(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)


def _select_field(records: list[dict], selected: str | None) -> str:
    for record in records:
        if set(record) & RESERVED_FIELDS or record.get("kind") in ("inspection", "ragvi-run"):
            raise ValueError(
                "Question/evaluation records and RAGvidence artifacts are not documents"
            )
    candidates = set().union(*(set(record) & TEXT_FIELDS for record in records))
    if selected is None:
        if len(candidates) != 1:
            raise ValueError("Ambiguous or missing document text field; use --text-field NAME")
        selected = next(iter(candidates))
    if any(not isinstance(row.get(selected), str) or not row[selected].strip() for row in records):
        raise ValueError(f"Every record must have nonempty string text in field {selected!r}")
    if any("\x00" in row[selected] for row in records):
        raise ValueError("Document text contains binary data")
    return selected


def extract_json(
    raw: bytes, *, jsonl: bool, text_field: str | None, max_records: int
) -> Extraction:
    text = decode_text(raw)
    if jsonl:
        numbered = [
            (number, line) for number, line in enumerate(text.splitlines(), 1) if line.strip()
        ]
        if len(numbered) > max_records:
            raise ValueError(f"Input exceeds the {max_records}-record limit")
        records = []
        locations = []
        for index, (number, line) in enumerate(numbered, 1):
            try:
                records.append(_json(line))
            except ValueError as exc:
                raise ValueError(f"Invalid JSONL at line {number}: {exc}") from exc
            locations.append({"record": index, "file_line": number})
    else:
        value = _json(text)
        records = value if isinstance(value, list) else [value]
        if len(records) > max_records:
            raise ValueError(f"Input exceeds the {max_records}-record limit")
        locations = [{"record": index} for index in range(1, len(records) + 1)]
    if not records or len(records) > max_records:
        raise ValueError(f"Require 1 to {max_records} document records")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError("Document JSON must be an object or an array of objects")
    field = _select_field(records, text_field)
    return Extraction(
        [
            ExtractedText(
                row[field],
                {**location, "text_field": field},
                {key: value for key, value in row.items() if key != field},
            )
            for row, location in zip(records, locations, strict=True)
        ],
        "jsonl-records-v1" if jsonl else "json-records-v1",
    )


def extract_csv(raw: bytes, *, text_field: str | None, max_records: int) -> Extraction:
    reader = csv.reader(io.StringIO(decode_text(raw), newline=""), strict=True)
    try:
        headers = next(reader, None)
        if (
            not headers
            or any(not header for header in headers)
            or len(set(headers)) != len(headers)
        ):
            raise ValueError("CSV requires unique, nonempty column names")
        rows, locations = [], []
        while True:
            start_line = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            if not values:
                continue
            index = len(rows) + 1
            if index > max_records:
                raise ValueError(f"Input exceeds the {max_records}-record limit")
            if len(values) != len(headers):
                raise ValueError(f"CSV row {index} does not match the header")
            rows.append(dict(zip(headers, values, strict=True)))
            locations.append(
                {
                    "row": index,
                    "file_line_start": start_line,
                    "file_line_end": reader.line_num,
                }
            )
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV: {exc}") from exc
    if not rows:
        raise ValueError("CSV has no document rows")
    field = _select_field(rows, text_field)
    return Extraction(
        [
            ExtractedText(
                row[field],
                {**location, "text_field": field},
                {key: value for key, value in row.items() if key != field},
            )
            for row, location in zip(rows, locations, strict=True)
        ],
        "csv-records-v1",
    )
