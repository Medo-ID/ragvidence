import pytest

from ragvidence.ingestion import load_corpus
from ragvidence.questions import load_questions


def test_markdown_passages_preserve_unicode_offsets_and_heading_paths(tmp_path):
    path = tmp_path / "manual.md"
    text = "# Device α\n\nGeneral instructions.\n## Reset\nHold for eight seconds.\n"
    path.write_bytes(text.encode("utf-8"))
    snapshot = load_corpus(path, exclude=[], size=28, overlap=4)
    document = snapshot.documents[0]
    assert document.body == text
    assert any(passage.heading_path == ["Device α", "Reset"] for passage in snapshot.passages)
    for passage in snapshot.passages:
        start, end = passage.metadata["source_start"], passage.metadata["source_end"]
        assert text[start:end] == passage.body
        assert len(passage.body) <= 28
        assert passage.metadata["origin_source_id"] == document.source_unit_id
        assert not passage.evidence_ids


def test_same_text_after_source_change_has_new_file_and_passage_identity(tmp_path):
    path = tmp_path / "manual.txt"
    path.write_text("First content")
    first = load_corpus(path, exclude=[])
    path.write_text("New content")
    second = load_corpus(path, exclude=[])
    assert first.corpus_hash != second.corpus_hash
    assert first.passages[0].source_unit_id != second.passages[0].source_unit_id


def test_mixed_folder_excludes_symlinks_hidden_files_and_generated_runs(tmp_path):
    (tmp_path / "manual.txt").write_text("Usable text")
    (tmp_path / ".env").write_text("secret")
    (tmp_path / "photo.jpg").write_bytes(b"binary")
    (tmp_path / "link.txt").symlink_to(tmp_path / "manual.txt")
    generated = tmp_path / "arbitrary-results"
    generated.mkdir()
    (generated / ".ragvi-run.json").write_text("{}")
    (generated / "report.md").write_text("Do not reindex generated reports")
    snapshot = load_corpus(tmp_path, exclude=[])
    assert len(snapshot.documents) == 1
    assert len(snapshot.skipped) == 4


@pytest.mark.parametrize("body", [b"", b" \n ", b"\xff\xff", b"a\x00b"])
def test_explicit_unusable_file_reports_an_error(tmp_path, body):
    path = tmp_path / "input.txt"
    path.write_bytes(body)
    with pytest.raises(ValueError, match="Cannot load"):
        load_corpus(path, exclude=[])


def test_bad_file_in_folder_is_reported_and_other_files_are_loaded(tmp_path):
    (tmp_path / "bad.txt").write_bytes(b"\xff")
    (tmp_path / "good.txt").write_text("Good text")
    snapshot = load_corpus(tmp_path, exclude=[])
    assert len(snapshot.documents) == 1
    assert snapshot.skipped[0].path == "bad.txt"


def test_discovery_and_size_limits_are_enforced(tmp_path):
    (tmp_path / "one.txt").write_text("Some content")
    (tmp_path / "two.md").write_text("More content")
    with pytest.raises(ValueError, match="file limit"):
        load_corpus(tmp_path, exclude=[], max_files=1)
    with pytest.raises(ValueError, match="total limit"):
        load_corpus(tmp_path, exclude=[], max_total_bytes=2)
    with pytest.raises(ValueError, match="byte limit"):
        load_corpus(tmp_path / "one.txt", exclude=[], max_file_bytes=2)


def test_question_file_ids_and_label_boundaries(tmp_path):
    path = tmp_path / "questions.jsonl"
    path.write_text('{"question_id":"Q","question":"Reset?"}\n')
    assert load_questions([], path)[0].question_id == "Q"
    path.write_text('{"question_id":"Q","question":"Reset?","reference_answer":"Eight"}\n')
    with pytest.raises(ValueError, match="reviewed"):
        load_questions([], path)
    path.write_text('{"question_id":"Q","question":"Reset?"}\n' * 2)
    with pytest.raises(ValueError, match="unique"):
        load_questions([], path)
