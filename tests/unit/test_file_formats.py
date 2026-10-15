import json
import sys
from pathlib import Path

import pytest

from ragvidence.ingestion import load_corpus

FIXTURES = Path(__file__).parents[1] / "fixtures/portable"


def assert_exact_spans(snapshot):
    documents = {document.source_unit_id: document for document in snapshot.documents}
    for passage in snapshot.passages:
        original = documents[passage.metadata["origin_source_id"]]
        assert (
            original.body[passage.metadata["source_start"] : passage.metadata["source_end"]]
            == passage.body
        )
        assert passage.metadata["location"] == original.metadata["location"]


def test_html_extracts_reviewed_visible_sections_with_heading_paths():
    snapshot = load_corpus(FIXTURES / "manual.html", exclude=[], size=30, overlap=3)
    assert [document.body for document in snapshot.documents] == [
        "Device & power\n\nUse USB-C power.",
        "Reset α\n\nHold for eight seconds.",
        "Pairing\n\nPress twice.",
    ]
    assert [document.heading_path for document in snapshot.documents] == [
        ["Device & power"],
        ["Device & power", "Reset α"],
        ["Device & power", "Pairing"],
    ]
    assert snapshot.documents[1].metadata["location"] == {"html_section": 2}
    assert snapshot.skipped[0].kind == "warning"
    assert_exact_spans(snapshot)


@pytest.mark.parametrize(
    "filename,field,second_location",
    [
        ("documents.json", "text", {"record": 2, "text_field": "text"}),
        ("documents.jsonl", "content", {"record": 2, "file_line": 3, "text_field": "content"}),
        (
            "documents.csv",
            "body",
            {"row": 2, "file_line_start": 4, "file_line_end": 4, "text_field": "body"},
        ),
    ],
)
def test_record_text_and_original_locations_are_independently_checked(
    filename, field, second_location
):
    snapshot = load_corpus(FIXTURES / filename, exclude=[], size=25, overlap=3)
    first, second = snapshot.documents
    assert first.body.startswith("Hold reset for eight seconds.")
    assert second.body == "Use USB-C power."
    assert second.metadata["location"] == second_location
    assert field not in first.metadata["record_metadata"]
    assert first.metadata["record_metadata"]["id"] == "reset"
    assert "category" not in first.body
    assert_exact_spans(snapshot)


@pytest.mark.parametrize(
    "extension,raw",
    [
        ("json", '{"text":"First", "body":"Second"}'),
        ("csv", "text,body\nFirst,Second\n"),
        ("jsonl", '{"custom":"First"}\n'),
    ],
)
def test_ambiguous_or_custom_text_requires_explicit_selection(tmp_path, extension, raw):
    path = tmp_path / f"input.{extension}"
    path.write_text(raw)
    with pytest.raises(ValueError, match="--text-field"):
        load_corpus(path, exclude=[])
    field = "custom" if extension == "jsonl" else "body"
    snapshot = load_corpus(path, exclude=[], text_field=field)
    assert snapshot.documents[0].body == ("First" if field == "custom" else "Second")
    assert snapshot.preparation.text_field == field


@pytest.mark.parametrize(
    "raw",
    [
        '{"question_id":"Q", "question":"Reset?", "text":"Gold answer"}',
        '{"text":"Gold answer", "reference_answer":"Eight seconds"}',
        '{"source_unit_id":"S", "body":"Workspace source"}',
        '{"kind":"inspection", "text":"A previous report"}',
        '{"manifest":{}, "queries":[], "text":"A previous run"}',
    ],
)
def test_artifacts_and_evaluation_records_cannot_be_reindexed(tmp_path, raw):
    path = tmp_path / "input.json"
    path.write_text(raw)
    with pytest.raises(ValueError, match="not documents"):
        load_corpus(path, exclude=[], text_field="text")


@pytest.mark.parametrize(
    "extension,raw,reason",
    [
        ("json", '{"text":"a","text":"b"}', "Duplicate"),
        ("json", '{"text":"a","value":NaN}', "Non-finite"),
        ("json", '[{"text":"a"},{"body":"b"}]', "Ambiguous"),
        ("json", '[{"text":"a"},{"text":1}]', "nonempty string"),
        ("json", "[]", "document records"),
        ("json", '["a"]', "array of objects"),
        ("jsonl", '{"text":"a"}\nnot-json', "line 2"),
        ("csv", "body,body\na,b\n", "unique"),
        ("csv", "body,id\na,b,c\n", "header"),
        ("csv", 'body,id\n"unclosed,b', "Invalid CSV"),
        ("html", "<script>Only script</script>", "visible text"),
    ],
)
def test_malformed_and_empty_inputs_fail_clearly(tmp_path, extension, raw, reason):
    path = tmp_path / f"bad.{extension}"
    path.write_text(raw)
    with pytest.raises(ValueError, match=reason):
        load_corpus(path, exclude=[])


def test_mixed_folder_notices_patterns_and_stable_order(tmp_path):
    (tmp_path / "b.json").write_text('{"text":"Second document"}')
    (tmp_path / "a.txt").write_text("First document")
    (tmp_path / "draft.txt").write_text("Ignore draft")
    (tmp_path / "broken.json").write_text("{broken}")
    (tmp_path / "questions.json").write_text('[{"question":"Secret question"}]')
    snapshot = load_corpus(
        tmp_path, exclude=[], include_patterns=["*.txt", "*.json"], exclude_patterns=["draft*"]
    )
    assert [document.body for document in snapshot.documents] == [
        "First document",
        "Second document",
    ]
    assert {notice.path: notice.kind for notice in snapshot.skipped} == {
        "draft.txt": "skipped",
        "broken.json": "failed",
        "questions.json": "failed",
    }
    assert (
        snapshot.model_dump()
        == load_corpus(
            tmp_path, exclude=[], include_patterns=["*.txt", "*.json"], exclude_patterns=["draft*"]
        ).model_dump()
    )


def test_records_and_total_extracted_character_budgets(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('[{"text":"First"},{"text":"Second"}]')
    with pytest.raises(ValueError, match="record limit"):
        load_corpus(path, exclude=[], max_records=1)
    (tmp_path / "b.txt").write_text("Third")
    with pytest.raises(ValueError, match="character extraction limit"):
        load_corpus(tmp_path, exclude=[], max_extracted_characters=12)


def test_missing_pdf_extra_has_actionable_error_without_download(tmp_path, monkeypatch):
    path = tmp_path / "document.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setitem(sys.modules, "pypdf", None)
    with pytest.raises(ValueError, match=r"ragvidence\[pdf\]"):
        load_corpus(path, exclude=[])


def test_json_custom_metadata_is_not_searchable(tmp_path):
    path = tmp_path / "input.json"
    path.write_text(
        json.dumps({"body": "Reset button", "metadata": {"nested": "DISTRACTOR"}, "kind": []})
    )
    snapshot = load_corpus(path, exclude=[])
    assert snapshot.documents[0].body == "Reset button"
    assert snapshot.documents[0].metadata["record_metadata"]["metadata"] == {"nested": "DISTRACTOR"}


def test_csv_blank_lines_do_not_shift_physical_record_start(tmp_path):
    path = tmp_path / "input.csv"
    path.write_text('body,id\n\n"First\nsecond",a\n\nThird,b\n')
    snapshot = load_corpus(path, exclude=[])
    assert snapshot.documents[0].metadata["location"] == {
        "row": 1,
        "file_line_start": 3,
        "file_line_end": 4,
        "text_field": "body",
    }
    assert snapshot.documents[1].metadata["location"] == {
        "row": 2,
        "file_line_start": 6,
        "file_line_end": 6,
        "text_field": "body",
    }


def test_trailing_newline_does_not_add_an_unreturned_line(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("First\nsecond\n")
    passage = load_corpus(path, exclude=[]).passages[0]
    assert passage.metadata["line_start"] == 1
    assert passage.metadata["line_end"] == 2
