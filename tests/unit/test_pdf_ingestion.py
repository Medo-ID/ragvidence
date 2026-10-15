"""Real parser checks against a PDF with literal, independently specified page text."""

from pathlib import Path

import pytest

from ragvidence.ingestion import load_corpus

pypdf = pytest.importorskip("pypdf", reason="Install the pdf extra for real parser tests")
FIXTURE = Path(__file__).parents[1] / "fixtures/portable/text-pages.pdf"


def test_real_pdf_pages_retain_text_locations_and_parser_version():
    snapshot = load_corpus(FIXTURE, exclude=[], size=20, overlap=2)
    assert [document.body.strip() for document in snapshot.documents] == [
        "Hold reset for eight seconds.",
        "Use USB-C power.",
    ]
    assert [document.metadata["location"] for document in snapshot.documents] == [
        {"page": 1},
        {"page": 3},
    ]
    assert all(pypdf.__version__ in document.metadata["loader"] for document in snapshot.documents)
    assert any("page 2" in notice.reason for notice in snapshot.skipped)
    documents = {document.source_unit_id: document for document in snapshot.documents}
    for passage in snapshot.passages:
        document = documents[passage.metadata["origin_source_id"]]
        assert (
            passage.body
            == document.body[passage.metadata["source_start"] : passage.metadata["source_end"]]
        )


def test_empty_and_encrypted_pdf_have_explicit_failures(tmp_path):
    blank = tmp_path / "blank.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=300, height=300)
    writer.write(blank)
    with pytest.raises(ValueError, match="no extractable text"):
        load_corpus(blank, exclude=[])
    writer.encrypt("secret-password")
    encrypted = tmp_path / "encrypted.pdf"
    writer.write(encrypted)
    with pytest.raises(ValueError, match="Encrypted"):
        load_corpus(encrypted, exclude=[])


def test_malformed_and_page_limited_pdf(tmp_path):
    invalid = tmp_path / "bad.pdf"
    invalid.write_bytes(b"This is not a PDF")
    with pytest.raises(ValueError, match="Cannot extract PDF"):
        load_corpus(invalid, exclude=[])
    with pytest.raises(ValueError, match="page limit"):
        load_corpus(FIXTURE, exclude=[], max_records=1)
    with pytest.raises(ValueError, match="character extraction limit"):
        load_corpus(FIXTURE, exclude=[], max_extracted_characters=10)
