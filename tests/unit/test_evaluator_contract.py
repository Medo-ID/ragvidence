from raglab.evaluation import evaluator
from raglab.models import (
    ExperimentRun,
    QueryRun,
    QuestionCase,
    RetrievalHit,
    RunManifest,
    StrategyConfig,
)


def test_evaluator_passes_required_evidence_before_ranked_hits(monkeypatch) -> None:
    observed = []

    def metric(required, ranking, k):
        observed.append((required, ranking, k))
        return True

    monkeypatch.setattr(evaluator, "sufficient_evidence_at_k", metric)
    monkeypatch.setattr(evaluator, "evidence_coverage_at_k", metric)
    monkeypatch.setattr(evaluator, "first_relevant_rank", metric)
    monkeypatch.setattr(evaluator, "reciprocal_rank", metric)
    monkeypatch.setattr(evaluator, "precision_at_k", metric)
    run = ExperimentRun(
        manifest=RunManifest(
            run_id="run",
            created_at="2026-10-05T00:00:00+00:00",
            product_version="0.1.0",
            python_version="3.12",
            platform="test",
            dataset_hash="hash",
            config=StrategyConfig(name="test", strategy="bm25", k=2),
            index_time_ms=0,
        ),
        queries=[
            QueryRun(
                question_id="Q-1",
                query_time_ms=0,
                hits=[RetrievalHit(source_unit_id="S-1", rank=1, score=1, evidence_ids={"E-1"})],
            )
        ],
    )
    question = QuestionCase(
        question_id="Q-1",
        question="Question?",
        split="dev",
        answerable=True,
        required_evidence_ids={"E-1"},
    )
    evaluator.evaluate_run(run, [question])
    assert observed == [({"E-1"}, [{"E-1"}], 2)] * 5
