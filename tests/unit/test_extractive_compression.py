import json

import pytest

from ragvidence.compression import compress_hits, lexical_spans
from ragvidence.config import Settings
from ragvidence.models import (
    CompressionConfig,
    RetrievalHit,
    SearchQuestion,
    SourceUnit,
    StrategyConfig,
)
from ragvidence.portable import run_portable
from ragvidence.providers.remote import ChatProvider


def test_lexical_selection_has_exact_offsets_and_original_order():
    body = "Reset once. Other facts! Reset again? Final unrelated text."
    spans = lexical_spans("reset", body, 2)
    assert [(s.start, s.end) for s in spans] == [(0, 11), (24, 37)]
    assert [body[s.start : s.end] for s in spans] == ["Reset once.", " Reset again?"]
    assert lexical_spans("unknown", body, 2) == []


def test_removing_a_qualification_loses_evidence_and_retains_original_offsets(tmp_path, m6_corpus):
    path, labels, snapshot = m6_corpus
    # Scoped retrieval removes the stale distractor. Sentence selection keeps duration,
    # but the qualifier has no lexical "reset" and must lose its evidence credit.
    from ragvidence.models import FilterConfig

    config = StrategyConfig(
        name="compressed",
        strategy="bm25",
        k=1,
        filters=FilterConfig(all=[{"field": "record_metadata.version", "op": "eq", "value": 2}]),
        compression=CompressionConfig(),
    )
    result = run_portable(
        path,
        [],
        config,
        output_root=tmp_path / "out",
        reviewed_file=labels,
        formats=["html", "markdown", "json"],
    )
    q = result.report["questions"][0]
    assert q["metrics"]["found_evidence_ids"] == ["DURATION"]
    assert q["metrics"]["missing_evidence_ids"] == ["CONDITION"]
    assert q["metrics"]["sufficient_evidence"] is False
    for hit in q["hits"]:
        original = next(
            d for d in snapshot.documents if d.source_unit_id == hit["origin_source_id"]
        )
        assert original.body[hit["start"] : hit["end"]] == hit["text"]
    assert q["hits"][0]["text"] == "Reset by holding for eight seconds."
    for export in result.exports.values():
        assert "CONDITION" in export.read_text() and "compression" in export.read_text()


def test_multiple_extracts_keep_one_hit_rank_and_precision_denominator(
    tmp_path, m6_corpus, monkeypatch
):
    from ragvidence.models import FilterConfig

    path, labels, snapshot = m6_corpus
    original = snapshot.documents[1]
    end_first = original.body.index(".") + 1
    start_second = original.body.index("Only")
    end_second = original.body.index(".", start_second) + 1

    def answer(self, system, user):
        data = json.loads(user)
        assert "GOLDSECRET" not in user
        source_id = next(
            s["source_unit_id"] for s in data["sources"] if "eight seconds" in s["body"]
        )
        return json.dumps(
            {
                "selections": [
                    {"source_unit_id": source_id, "start": 0, "end": end_first},
                    {"source_unit_id": source_id, "start": start_second, "end": end_second},
                ]
            }
        )

    monkeypatch.setattr(ChatProvider, "answer", answer)
    result = run_portable(
        path,
        [],
        StrategyConfig(
            name="model",
            strategy="bm25",
            k=1,
            filters=FilterConfig(
                all=[{"field": "record_metadata.version", "op": "eq", "value": 2}]
            ),
            compression=CompressionConfig(mode="model", model="fixture"),
        ),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    q = result.report["questions"][0]
    assert len(q["hits"]) == 2 and {h["rank"] for h in q["hits"]} == {1}
    assert q["metrics"]["sufficient_evidence"] is True
    assert q["metrics"]["reciprocal_rank"] == 1 and q["metrics"]["precision_at_k"] == 1
    run = json.loads((result.directory / "run.json").read_text())
    assert len(run["queries"][0]["hits"]) == 1 and len(run["queries"][0]["context"]) == 2
    assert run["queries"][0]["returned_context_characters"] == end_first + end_second - start_second


@pytest.mark.parametrize(
    "selections",
    [
        [{"source_unit_id": "unknown", "start": 0, "end": 3}],
        [{"source_unit_id": "S", "start": 0, "end": 100}],
        [{"source_unit_id": "S", "start": True, "end": 3}],
        [
            {"source_unit_id": "S", "start": 2, "end": 3},
            {"source_unit_id": "S", "start": 0, "end": 1},
        ],
        [
            {"source_unit_id": "S", "start": 0, "end": 3},
            {"source_unit_id": "S", "start": 2, "end": 4},
        ],
        [{"source_unit_id": "S", "start": 0, "end": 3, "text": "fabricated"}],
        [
            {"source_unit_id": "S", "start": 0, "end": 1},
            {"source_unit_id": "S", "start": 2, "end": 3},
            {"source_unit_id": "S", "start": 4, "end": 5},
        ],
    ],
)
def test_invalid_model_spans_fail_or_explicitly_fall_back(monkeypatch, selections):
    monkeypatch.setattr(
        ChatProvider, "answer", lambda *args: json.dumps({"selections": selections})
    )
    source = SourceUnit(source_unit_id="S", document_id="D", body="Reset.")
    hit = RetrievalHit(source_unit_id="S", rank=1, score=1.0)
    with pytest.raises(RuntimeError, match="no retrieval was scored"):
        compress_hits(
            "reset",
            [hit],
            {"S": source},
            CompressionConfig(mode="model", model="fixture"),
            Settings(_env_file=None),
        )
    selected, stage = compress_hits(
        "reset",
        [hit],
        {"S": source},
        CompressionConfig(mode="model", model="fixture", failure="original"),
        Settings(_env_file=None),
    )
    assert selected == [hit] and stage.details["state"] == "fallback_original"


def test_parent_expansion_precedes_compression_and_budget_counts_only_exact_extracts(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text(
        "Noise noise noise noise noise. Reset for eight seconds. More irrelevant text."
    )
    config = StrategyConfig(
        name="parent",
        strategy="bm25",
        k=1,
        child_splitter="recursive",
        child_size=12,
        child_overlap=0,
        compression=CompressionConfig(),
    )
    result = run_portable(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        config,
        output_root=tmp_path / "out",
    )
    q = result.report["questions"][0]
    names = [stage["name"] for stage in q["stages"]]
    assert (
        names.index("parent_expansion")
        < names.index("compression")
        < names.index("context_selection")
    )
    assert q["hits"][0]["text"] == " Reset for eight seconds."
    run = json.loads((result.directory / "run.json").read_text())
    assert q["context_measurement"]["count"] == len(run["queries"][0]["rendered_context"])
    config.context_budget = 1
    limited = run_portable(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        config,
        output_root=tmp_path / "out",
    )
    assert limited.report["questions"][0]["hits"] == []


def test_empty_model_selection_is_valid_and_has_no_context(tmp_path, m6_corpus, monkeypatch):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: '{"selections":[]}')
    result = run_portable(
        m6_corpus[0],
        [],
        StrategyConfig(
            name="empty",
            strategy="bm25",
            compression=CompressionConfig(mode="model", model="fixture"),
        ),
        output_root=tmp_path / "out",
        reviewed_file=m6_corpus[1],
    )
    q = result.report["questions"][0]
    assert q["hits"] == [] and q["metrics"]["evidence_coverage"] == 0


def test_compression_can_recover_evidence_under_a_fixed_character_budget(tmp_path, m6_corpus):
    from ragvidence.models import FilterConfig

    path, labels, _ = m6_corpus
    references = json.loads(labels.read_text())
    for question in references["questions"]:
        question["required_evidence_ids"] = ["DURATION"]
    labels.write_text(json.dumps(references))
    config = StrategyConfig(
        name="budget",
        strategy="bm25",
        k=1,
        context_budget=80,
        filters=FilterConfig(all=[{"field": "record_metadata.version", "op": "eq", "value": 2}]),
    )
    baseline = run_portable(path, [], config, output_root=tmp_path / "out", reviewed_file=labels)
    compressed = run_portable(
        path,
        [],
        config.model_copy(update={"compression": CompressionConfig()}),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    assert baseline.report["questions"][0]["metrics"]["sufficient_evidence"] is False
    assert compressed.report["questions"][0]["metrics"]["sufficient_evidence"] is True
    assert compressed.report["questions"][0]["context_measurement"]["count"] <= 80
