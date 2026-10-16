import json
import math

import numpy as np
import pytest

from ragvidence.models import MMRConfig, RetrievalHit, SearchQuestion, StrategyConfig
from ragvidence.portable import run_portable
from ragvidence.selection import select_mmr


def hits():
    return [
        RetrievalHit(source_unit_id=name, rank=i, score=float(10 - i))
        for i, name in enumerate("ABC", 1)
    ]


@pytest.mark.parametrize("weight,order", [(1.0, "ABC"), (0.0, "ACB"), (0.3, "ACB")])
def test_mmr_matches_independent_two_dimension_oracle(weight, order):
    # A and B duplicate one another; C has relevance .6 and complementary direction.
    selected = select_mmr(hits(), [[1, 0], [1, 0], [0.6, 0.8]], [1, 0], lambda_mult=weight, k=3)
    assert "".join(h.source_unit_id for h in selected) == order
    assert selected[0].score == pytest.approx(weight)
    c = next(h for h in selected if h.source_unit_id == "C")
    assert c.score == pytest.approx(weight * 0.6 - (1 - weight) * 0.6)
    assert c.metadata["mmr"]["input_rank"] == 3
    assert c.metadata["mmr"]["input_score"] == 7
    assert c.metadata["mmr"]["redundancy"] == pytest.approx(0.6)


@pytest.mark.parametrize(
    "vectors,query",
    [
        ([[0, 0], [1, 0], [0, 1]], [1, 0]),
        ([[1, 0], [1, 0], [0, 1]], [0, 0]),
        ([[math.nan, 0], [1, 0], [0, 1]], [1, 0]),
        ([[1, 0]], [1, 0]),
        ([[1, 0], [1, 0], [0, 1]], [1, 0, 0]),
    ],
)
def test_mmr_rejects_invalid_embeddings(vectors, query):
    with pytest.raises((ValueError, RuntimeError)):
        select_mmr(hits(), vectors, query, lambda_mult=0.5, k=2)


def test_mmr_empty_uniqueness_limits_and_stable_ties():
    assert select_mmr([], [], [], lambda_mult=0.5, k=2) == []
    pool = hits()
    assert len(select_mmr(pool, np.eye(3), [1, 1, 1], lambda_mult=1, k=20)) == 3
    assert [
        h.source_unit_id for h in select_mmr(pool, np.eye(3), [1, 1, 1], lambda_mult=1, k=2)
    ] == ["A", "B"]
    with pytest.raises(ValueError, match="unique"):
        select_mmr([pool[0], pool[0]], [[1, 0], [1, 0]], [1, 0], lambda_mult=0.5, k=2)


def test_mmr_runs_after_reranking_with_bounded_candidates_and_identity(
    tmp_path,
    m6_corpus,
    m6_embeddings,
    monkeypatch,
):
    from ragvidence import runner

    observed = []

    class Reranker:
        def __init__(self, *args, **kwargs):
            pass

        def rerank(self, question, pool, texts, k):
            observed.append((question, [h.source_unit_id for h in pool]))
            return [h.model_copy(update={"rank": i}) for i, h in enumerate(reversed(pool), 1)]

    monkeypatch.setattr(runner, "FastEmbedReranker", Reranker)
    result = run_portable(
        m6_corpus[0],
        [SearchQuestion(question_id="Q", question="reset")],
        StrategyConfig(
            name="diverse",
            strategy="bm25",
            k=2,
            reranker_model="fixture",
            rerank_k=2,
            mmr=MMRConfig(candidates=3),
        ),
        output_root=tmp_path / "out",
        cache_dir=tmp_path / "cache",
    )
    q = result.report["questions"][0]
    stages = {stage["name"]: stage for stage in q["stages"]}
    assert len(observed[0][1]) == 2
    assert stages["mmr"]["details"]["input_ids"] == list(reversed(observed[0][1]))
    assert stages["mmr"]["details"]["embedding_identity"]["revision"] == "1"
    assert len(q["hits"]) == 2 and stages["mmr"]["elapsed_ms"] >= 0
    assert q["context_measurement"]["count"] > 0


@pytest.mark.parametrize("helpful", [True, False])
def test_diversity_can_recover_complementary_evidence_or_drop_a_required_duplicate(
    tmp_path,
    monkeypatch,
    helpful,
):
    from ragvidence import pipeline
    from ragvidence.ingestion import load_corpus
    from ragvidence.strategies.semantic import SemanticStrategy

    path = tmp_path / "documents.json"
    path.write_text(
        json.dumps(
            [
                {"text": "Reset for eight seconds."},
                {"text": "Reset for eight seconds with calibration."},
                {"text": "Disconnect power before reset."},
            ]
        )
    )
    snapshot = load_corpus(path, exclude=[])
    evidence = []
    for index in (0, 2 if helpful else 1):
        source = snapshot.documents[index]
        evidence.append(
            {
                "evidence_id": str(index),
                "spans": [
                    {
                        "source_id": source.source_unit_id,
                        "start": 0,
                        "end": len(source.body),
                        "text": source.body,
                    }
                ],
            }
        )
    labels = tmp_path / "reviewed.json"
    labels.write_text(
        json.dumps(
            {
                "corpus_hash": snapshot.corpus_hash,
                "evidence": evidence,
                "questions": [
                    {
                        "question_id": "Q",
                        "question": "reset",
                        "split": "dev",
                        "answerable": True,
                        "required_evidence_ids": [item["evidence_id"] for item in evidence],
                    }
                ],
            }
        )
    )

    class Embeddings:
        model_name = "two-dimensional-oracle"

        def embed_documents(self, texts):
            return np.array([[1, 0] if "eight seconds" in text else [0.6, 0.8] for text in texts])

        def embed_query(self, query):
            return np.array([1, 0])

    monkeypatch.setattr(
        pipeline, "semantic_strategy", lambda *args: SemanticStrategy(provider=Embeddings())
    )
    config = StrategyConfig(name="baseline", strategy="semantic", k=2)
    baseline = run_portable(path, [], config, output_root=tmp_path / "out", reviewed_file=labels)
    diverse = run_portable(
        path,
        [],
        config.model_copy(update={"mmr": MMRConfig(lambda_mult=0.3, candidates=3)}),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    assert baseline.report["questions"][0]["metrics"]["sufficient_evidence"] is (not helpful)
    assert diverse.report["questions"][0]["metrics"]["sufficient_evidence"] is helpful
