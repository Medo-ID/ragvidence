import json

import pytest

from ragvidence.budgets import ContextCounter, select_context
from ragvidence.context import passages_for_hits, render_context
from ragvidence.models import RetrievalHit, SourceUnit


def test_budget_counts_ids_headings_and_separators_and_skips_oversized_passages():
    sources = {
        name: SourceUnit(source_unit_id=name, document_id="D", body=body, heading_path=["Heading"])
        for name, body in [("A", "x" * 100), ("B", "small"), ("C", "tiny")]
    }
    hits = [
        RetrievalHit(source_unit_id=name, rank=rank, score=1.0)
        for rank, name in enumerate(sources, 1)
    ]
    counter = ContextCounter()
    one = counter.count(render_context(passages_for_hits([hits[1]], sources)))
    selected, measurement = select_context(hits, sources, k=2, budget=one, counter=counter)
    assert [hit.source_unit_id for hit in selected] == ["B"]
    assert selected[0].rank == 1
    assert measurement["count"] == one > len("small")
    assert [item["source_unit_id"] for item in measurement["skipped"]] == ["A", "C"]
    assert counter.identity["unit"] == "characters" and counter.identity["exact"] is True


def test_budget_can_return_empty_context_without_fabricated_evidence():
    source = SourceUnit(source_unit_id="A", document_id="D", body="Large")
    hits, measurement = select_context(
        [RetrievalHit(source_unit_id="A", rank=1, score=1.0)],
        {"A": source},
        k=1,
        budget=1,
        counter=ContextCounter(),
    )
    assert hits == [] and measurement["count"] == 0


def test_real_local_tokenizer_identity_and_exact_count(tmp_path):
    tokenizers = pytest.importorskip("tokenizers")
    tokenizer = tokenizers.Tokenizer(
        tokenizers.models.WordLevel({"[UNK]": 0, "reset": 1, "button": 2}, unk_token="[UNK]")
    )
    tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.Whitespace()
    tokenizer.enable_truncation(max_length=2)
    tokenizer.enable_padding(length=8)
    path = tmp_path / "tokenizer.json"
    path.write_text(tokenizer.to_str())
    counter = ContextCounter(str(path))
    assert counter.count("reset button") == 2
    assert counter.count("reset button reset button") == 4
    assert counter.identity["unit"] == "tokens"
    identity = counter.identity["file_hash"]
    path.write_text(json.dumps({"changed": True}))
    with pytest.raises(ValueError, match="changed"):
        ContextCounter(str(path), identity)
