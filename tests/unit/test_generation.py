from ragvidence.config import Settings
from ragvidence.data import load_dataset
from ragvidence.generation import generate_answers
from ragvidence.models import StrategyConfig
from ragvidence.runner import run_experiment
from ragvidence.workspace import EXERCISE_ROOT


def test_generation_uses_validated_recorded_context(monkeypatch):
    from ragvidence import generation

    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="answers", strategy="bm25"))
    observed = []

    class Chat:
        def __init__(self, *args):
            pass

        def answer(self, system, user):
            observed.append(user)
            return "For inspection only"

    monkeypatch.setattr(generation, "ChatProvider", Chat)
    settings = Settings(
        _env_file=None,
        generation_provider="ollama",
        generation_model="fake",
        generation_base_url="http://localhost:11434",
    )
    answers = generate_answers(EXERCISE_ROOT, run, settings)
    assert len(answers["answers"]) == len(run.queries)
    assert all(
        message.endswith(query.rendered_context)
        for message, query in zip(observed, run.queries, strict=True)
    )
    for answer, message in zip(answers["answers"], observed, strict=True):
        measurement = answer["request_measurement"]
        assert measurement["count"] == len(generation.SYSTEM_PROMPT) + len(message)
        assert measurement["scope"] == "complete_message_contents"
        assert measurement["provider_framing_count"] is None


def test_retrieval_stages_do_not_receive_gold_labels(monkeypatch):
    from ragvidence import runner
    from ragvidence.strategies.bm25 import BM25Strategy

    class InspectingStrategy(BM25Strategy):
        def index(self, records):
            assert all(not record.source.evidence_ids for record in records)
            super().index(records)

    monkeypatch.setattr(runner, "build_strategy", lambda *args: InspectingStrategy())
    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="no-leak", strategy="bm25"))
    sources, _ = load_dataset(EXERCISE_ROOT)
    authoritative = {source.source_unit_id: source.evidence_ids for source in sources}
    assert all(
        hit.evidence_ids == authoritative[hit.source_unit_id]
        for query in run.queries
        for hit in query.hits
    )
