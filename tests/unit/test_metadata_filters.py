import json

import pytest

from ragvidence.filtering import matches
from ragvidence.models import FilterConfig, MetadataPredicate, SearchQuestion, StrategyConfig
from ragvidence.portable import run_portable


@pytest.mark.parametrize(
    "metadata,op,value,expected",
    [
        ({"v": 2}, "eq", 2.0, True),
        ({"v": True}, "eq", 1, False),
        ({"v": "2"}, "eq", 2, False),
        ({"v": None}, "eq", None, True),
        ({}, "eq", None, False),
        ({"v": [2]}, "in", [2], False),
        ({"v": 2}, "in", [True, "2", 2], True),
        ({"v": False}, "in", [0], False),
        ({"v": 2}, "gt", 2, False),
        ({"v": 2}, "gte", 2, True),
        ({"v": 2.5}, "lt", 3, True),
        ({"v": 3}, "lte", 3.0, True),
        ({"v": "2026-01"}, "gte", "2025-12", True),
        ({"v": "2"}, "gt", 1, False),
        ({"v": {"nested": 3}}, "eq", 3, False),
    ],
)
def test_typed_predicate_truth_table(metadata, op, value, expected):
    assert matches(metadata, MetadataPredicate(field="v", op=op, value=value)) is expected


@pytest.mark.parametrize(
    "field,op,value",
    [
        ("", "eq", 2),
        ("a..b", "eq", 2),
        ("a", "in", []),
        ("a", "in", 2),
        ("a", "eq", [2]),
        ("a", "gt", True),
        ("a", "eq", float("nan")),
    ],
)
def test_invalid_predicates_are_rejected(field, op, value):
    with pytest.raises(ValueError):
        MetadataPredicate(field=field, op=op, value=value)


@pytest.mark.parametrize("strategy,parent", [("bm25", False), ("hybrid", False), ("hybrid", True)])
def test_filters_precede_ranking_variants_and_parent_expansion(
    tmp_path,
    m6_corpus,
    m6_embeddings,
    strategy,
    parent,
):
    path, labels, snapshot = m6_corpus
    config = StrategyConfig(
        name="scoped",
        strategy=strategy,
        k=1,
        child_splitter="recursive" if parent else "none",
        child_size=12,
        child_overlap=0,
        filters=FilterConfig(
            all=[{"field": "record_metadata.version", "op": "gte", "value": 2}],
            questions={
                "Q": [{"field": "record_metadata.product", "op": "in", "value": ["A"]}],
                "H": [{"field": "record_metadata.product", "op": "in", "value": ["A"]}],
            },
        ),
        query_variants={"Q": ["one second", "reset button"]},
    )
    result = run_portable(path, [], config, output_root=tmp_path / "out", reviewed_file=labels)
    for q in result.report["questions"]:
        assert len(q["hits"]) == 1
        assert q["hits"][0]["origin_source_id"] == snapshot.documents[1].source_unit_id
        assert q["metrics"]["sufficient_evidence"] is True
        assert q["stages"][0]["name"] == "metadata_filter"
        assert q["stages"][0]["details"]["eligible_count"] == 1
    assert not any("one second." in text for text in m6_embeddings)
    assert "GOLDSECRET" not in " ".join(m6_embeddings)


def test_empty_filter_and_unknown_question_id_are_explicit(tmp_path, m6_corpus, monkeypatch):
    from ragvidence import runner

    path, _, _ = m6_corpus
    monkeypatch.setattr(
        runner, "build_strategy", lambda *args: pytest.fail("Empty scope must not rank")
    )
    config = StrategyConfig(
        name="empty",
        strategy="bm25",
        filters=FilterConfig(
            all=[
                {"field": "missing", "op": "eq", "value": None},
            ]
        ),
    )
    result = run_portable(
        path,
        [SearchQuestion(question_id="Q", question="reset")],
        config,
        output_root=tmp_path / "out",
    )
    assert result.report["questions"][0]["hits"] == []
    assert "excluded every source" in " ".join(result.report["questions"][0]["observations"])
    config.filters.questions["UNKNOWN"] = []
    with pytest.raises(RuntimeError, match="unknown question"):
        run_portable(path, [], config, output_root=tmp_path / "out")


def test_question_scopes_do_not_reuse_the_wrong_index(tmp_path, m6_corpus):
    path, _, snapshot = m6_corpus
    filters = FilterConfig(
        questions={
            q: [{"field": "record_metadata.version", "op": "eq", "value": version}]
            for q, version in (("old", 1), ("new", 2))
        }
    )
    result = run_portable(
        path,
        [SearchQuestion(question_id=q, question="reset") for q in ("old", "new")],
        StrategyConfig(name="versions", strategy="bm25", k=1, filters=filters),
        output_root=tmp_path / "out",
    )
    assert [q["hits"][0]["origin_source_id"] for q in result.report["questions"]] == [
        d.source_unit_id for d in snapshot.documents[:2]
    ]
    saved = json.loads((result.directory / "run.json").read_text())
    assert saved["manifest"]["config"]["filters"] == filters.model_dump()
