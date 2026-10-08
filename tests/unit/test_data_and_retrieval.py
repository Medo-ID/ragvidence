from pathlib import Path

from raglab.data import load_dataset
from raglab.representation import build_records
from raglab.strategies.bm25 import BM25Strategy, tokenize
from raglab.workspace import EXERCISE_ROOT, create_workspace, restore_workspace


def test_bundled_dataset_has_reviewed_evidence() -> None:
    sources, questions = load_dataset(EXERCISE_ROOT)
    assert len(sources) == 8
    assert len(questions) == 12


def test_tokenizer_preserves_version_and_identifier_tokens() -> None:
    assert tokenize("Firmware 4.2 SKU-7722XX") == ["firmware", "4.2", "sku-7722xx"]


def test_heading_representation_adds_only_source_heading() -> None:
    sources, _ = load_dataset(EXERCISE_ROOT)
    body = build_records(sources, "body")[0]
    heading = build_records(sources, "heading_context")[0]
    assert body.source == heading.source
    assert heading.searchable_text.endswith(body.searchable_text)
    assert "Orion DeskHub > Firmware 4.2" in heading.searchable_text


def test_bm25_returns_ranked_source_evidence() -> None:
    sources, _ = load_dataset(EXERCISE_ROOT)
    strategy = BM25Strategy()
    strategy.index(build_records(sources, "heading_context"))
    hits = strategy.search("Orion DeskHub firmware 4.2 pairing reset", k=2)
    assert [hit.rank for hit in hits] == [1, 2]
    assert "SEC-ORION-42-RESET" in {hit.source_unit_id for hit in hits}


def test_workspace_restore_preserves_backup(tmp_path: Path) -> None:
    target = create_workspace(tmp_path, "demo")
    (target / "notes.txt").write_text("user edit")
    restored, backup = restore_workspace(tmp_path, "demo")
    assert restored.is_dir()
    assert (backup / "notes.txt").read_text() == "user edit"
