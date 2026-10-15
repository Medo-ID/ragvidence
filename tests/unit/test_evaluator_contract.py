from ragvidence.artifacts import HASH_ALGORITHM, content_hash
from ragvidence.context import context_fields
from ragvidence.evaluation import evaluator
from ragvidence.models import (
    ExperimentRun,
    QueryRun,
    QuestionCase,
    RetrievalHit,
    RunManifest,
    SourceUnit,
    StrategyConfig,
)
from ragvidence.provenance import (
    corpus_identity,
    question_identity,
    reference_identity,
    representation_identity,
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
    sources = [SourceUnit(source_unit_id="S-1", document_id="D", body="fact", evidence_ids={"E-1"})]
    run.manifest.schema_version = 2
    run.manifest.hash_algorithm = HASH_ALGORITHM
    run.manifest.dataset_hash = content_hash({"sources": sources, "questions": [question]})
    run.manifest.corpus_hash = corpus_identity(sources)
    run.manifest.questions_hash = question_identity([question])
    run.manifest.references_hash = reference_identity(sources, [question])
    run.manifest.configuration_hash = content_hash(run.manifest.config)
    run.manifest.representation_hash = representation_identity(sources, run.manifest.config)
    run.queries[0] = run.queries[0].model_copy(
        update=context_fields(
            run.queries[0].hits, {source.source_unit_id: source for source in sources}
        )
    )
    evaluator.evaluate_run(run, [question], sources=sources)
    assert observed == [({"E-1"}, [{"E-1"}], 2)] * 5
