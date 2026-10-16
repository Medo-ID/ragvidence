import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from ragvidence.chunking import child_spans
from ragvidence.cli import app
from ragvidence.diagnosis import diagnose
from ragvidence.evaluation.evaluator import evaluate_run
from ragvidence.models import RetrievalHit, SourceUnit, StrategyConfig
from ragvidence.representation import build_records
from ragvidence.reranking import FastEmbedReranker
from ragvidence.runner import run_experiment
from ragvidence.strategies.bm25 import BM25Strategy
from ragvidence.strategies.hybrid import HybridStrategy, fuse_rankings
from ragvidence.strategies.parent_child import ParentChildStrategy
from ragvidence.workspace import EXERCISE_ROOT, create_workspace


def hit(source_id, rank, score=1):
    return RetrievalHit(
        source_unit_id=source_id, rank=rank, score=score, evidence_ids={f"E-{source_id}"}
    )


class FixedStrategy:
    def __init__(self, hits):
        self.hits = hits
        self.depths = []

    def index(self, records):
        self.records = list(records)

    def search(self, query, *, k):
        self.depths.append(k)
        return self.hits[:k]


def test_rrf_uses_ranks_weights_and_one_contribution_per_source():
    fused = fuse_rankings(
        [[hit("A", 1, 999), hit("A", 2), hit("B", 3)], [hit("B", 1, -999)]],
        k=2,
        constant=0,
        weights=[0.25, 0.75],
    )
    assert [item.source_unit_id for item in fused] == ["B", "A"]
    assert fused[0].score == pytest.approx(0.25 / 3 + 0.75)
    assert fused[1].score == 0.25
    assert [item.rank for item in fused] == [1, 2]
    assert fused[0].evidence_ids == {"E-B"}
    assert len(fused[0].metadata["rrf_contributions"]) == 2


def test_rrf_stable_ties_and_missing_lists():
    assert [
        item.source_unit_id for item in fuse_rankings([[hit("Z", 1)], [], [hit("A", 1)]], k=3)
    ] == ["Z", "A"]


def test_hybrid_fetches_candidates_before_final_cutoff():
    lexical = FixedStrategy([hit("A", 1), hit("B", 2)])
    semantic = FixedStrategy([hit("C", 1), hit("B", 2)])
    hybrid = HybridStrategy(lexical, semantic, candidate_k=2)
    hybrid.index([])
    hits = hybrid.search("question", k=1)
    assert hits[0].source_unit_id == "B"
    assert lexical.depths == semantic.depths == [2]


@pytest.mark.parametrize("splitter", ["recursive", "markdown"])
@pytest.mark.parametrize("size,overlap", [(1, 0), (17, 0), (17, 16), (100, 10)])
def test_children_preserve_all_characters_and_size_bounds(splitter, size, overlap):
    text = "# Start\n\nSome αβγ words.\nNext line\n## End\n" + "x" * 113
    spans = child_spans(text, size=size, overlap=overlap, splitter=splitter)
    coverage = set()
    for start, end in spans:
        assert 0 <= start < end <= len(text)
        assert end - start <= size
        coverage.update(range(start, end))
    assert coverage == set(range(len(text)))
    assert [start for start, _ in spans] == sorted({start for start, _ in spans})


def test_markdown_keeps_heading_boundaries_and_ignores_fenced_headings():
    text = "# One\nText\n```python\n# not a heading\n```\n## Two\nMore\n"
    spans = child_spans(text, size=200, overlap=0, splitter="markdown")
    assert [text[start:end] for start, end in spans] == text.split("## Two")[0:1] + [
        "## Two\nMore\n"
    ]


def test_parent_child_returns_full_parent_labels_without_duplicates():
    parent = SourceUnit(
        source_unit_id="P",
        document_id="D",
        body="first fact\n\nsecond fact",
        evidence_ids={"E1", "E2"},
    )
    base = FixedStrategy([hit("child-0", 1), hit("child-1", 2)])
    strategy = ParentChildStrategy(base, splitter="recursive", size=12, overlap=0, candidate_k=8)
    strategy.index(build_records([parent], "body"))
    assert all(not record.source.evidence_ids for record in base.records)
    hits = strategy.search("fact", k=2)
    assert len(hits) == 1
    assert hits[0].source_unit_id == "P"
    assert hits[0].evidence_ids == {"E1", "E2"}
    assert hits[0].preview == parent.body
    assert hits[0].metadata["returned_context"] == "full_parent"
    assert base.depths == [8]


def test_context_prefix_is_searchable_without_mutating_evidence():
    source = SourceUnit(
        source_unit_id="S",
        document_id="D",
        body="Eight seconds.",
        evidence_ids={"E"},
        metadata={"context_prefix": "Orion 4.2 reset"},
    )
    record = build_records([source], "contextual")[0]
    assert record.searchable_text == "Orion 4.2 reset\n\nEight seconds."
    assert source.body == "Eight seconds."
    assert record.source.evidence_ids == {"E"}


def test_contextual_requires_valid_prefix_for_every_source():
    source = SourceUnit(source_unit_id="S", document_id="D", body="body")
    with pytest.raises(ValueError, match="context_prefix"):
        build_records([source], "contextual")


def test_multiquery_deduplicates_queries_and_retains_original_question(monkeypatch):
    observed = []

    def search(self, query, *, k):
        observed.append(query)
        return [hit("SEC-ORION-42-RESET", 1)]

    monkeypatch.setattr(BM25Strategy, "search", search)
    run = run_experiment(
        EXERCISE_ROOT,
        StrategyConfig(
            name="variants",
            strategy="bm25",
            k=1,
            query_variants={"DEV-01": [" reset pairing ", "reset pairing"]},
        ),
    )
    assert run.queries[0].search_queries == [observed[0], "reset pairing"]
    assert observed.count("reset pairing") == 1
    assert run.manifest.config.candidate_k == 20
    assert len(run.queries) == 12


@pytest.mark.parametrize(
    "options",
    [
        {"k": 3, "candidate_k": 2},
        {"child_splitter": "recursive", "child_size": 4, "child_overlap": 4},
        {"query_variants": {"Q": [" "]}},
        {"lexical_weight": 0},
        {"lexical_weight": 1},
        {"rrf_constant": -1},
    ],
)
def test_invalid_pipeline_options_fail_validation(options):
    with pytest.raises(ValidationError):
        StrategyConfig(name="invalid", strategy="bm25", **options)


def test_unknown_query_variants_and_imported_strategy_rejected_before_indexing():
    with pytest.raises(ValueError, match="unknown question IDs"):
        run_experiment(
            EXERCISE_ROOT,
            StrategyConfig(name="unknown", strategy="bm25", query_variants={"TYPO": ["query"]}),
        )
    with pytest.raises(ValueError, match="import-run"):
        run_experiment(EXERCISE_ROOT, StrategyConfig(name="import", strategy="imported"))


def fake_reranker(monkeypatch, scores):
    module = ModuleType("fastembed.rerank.cross_encoder")

    class Encoder:
        def __init__(self, model_name):
            assert model_name == "test-model"

        def rerank(self, query, documents):
            assert query == "question"
            assert documents == ["complete A passage", "complete B passage"]
            return iter(scores)

    module.TextCrossEncoder = Encoder
    monkeypatch.setitem(sys.modules, "fastembed.rerank.cross_encoder", module)
    return FastEmbedReranker("test-model")


def test_cross_encoder_uses_complete_context_and_preserves_prior_ranking(monkeypatch):
    reranker = fake_reranker(monkeypatch, [0.1, 0.9])
    hits = reranker.rerank(
        "question",
        [hit("A", 1), hit("B", 2)],
        {"A": "complete A passage", "B": "complete B passage"},
        k=1,
    )
    assert hits[0].source_unit_id == "B"
    assert hits[0].rank == 1 and hits[0].score == 0.9
    assert hits[0].metadata["before_rerank_rank"] == 2
    assert hits[0].evidence_ids == {"E-B"}


@pytest.mark.parametrize("scores", [[float("nan"), 1], [1], [1, float("inf")]])
def test_cross_encoder_rejects_invalid_scores(monkeypatch, scores):
    reranker = fake_reranker(monkeypatch, scores)
    with pytest.raises(RuntimeError, match="invalid scores"):
        reranker.rerank(
            "question",
            [hit("A", 1), hit("B", 2)],
            {"A": "complete A passage", "B": "complete B passage"},
            k=2,
        )


def test_experiment_cli_evaluates_parent_context_and_does_not_overwrite(tmp_path: Path):
    workspace = create_workspace(tmp_path, "lab")
    config = tmp_path / "pipeline.json"
    config.write_text(
        json.dumps(
            {
                "name": "parent",
                "strategy": "bm25",
                "representation": "heading_context",
                "child_splitter": "markdown",
                "child_size": 90,
                "child_overlap": 10,
                "k": 2,
            }
        )
    )
    runner = CliRunner()
    result = runner.invoke(app, ["experiment", str(workspace), str(config)])
    assert result.exit_code == 0, result.output
    run_path = workspace / "runs/parent.json"
    before = run_path.read_bytes()
    assert runner.invoke(app, ["evaluate", str(workspace), str(run_path)]).exit_code == 0
    evaluation = json.loads((workspace / "evaluations/parent.json").read_text())
    assert evaluation["questions"][0]["search_queries"]
    assert evaluation["questions"][0]["returned_context_characters"] > 0
    repeat = runner.invoke(app, ["experiment", str(workspace), str(config)])
    assert repeat.exit_code == 1 and "overwrite" in repeat.output
    assert run_path.read_bytes() == before


def test_experiment_cli_rejects_path_names_without_traceback(tmp_path):
    config = tmp_path / "invalid.json"
    config.write_text('{"name":"../escape","strategy":"bm25"}')
    result = CliRunner().invoke(app, ["experiment", str(tmp_path), str(config)])
    assert result.exit_code == 1
    assert "name" in result.output
    assert "Traceback" not in result.output


def test_hybrid_improvement_diagnosis_does_not_claim_heading_cause():
    result = diagnose(
        {
            "baseline": {"strategy": "bm25", "representation": "body"},
            "intervention": {"strategy": "hybrid", "representation": "heading_context"},
            "summary": {"fail_to_pass": 2, "pass_to_fail": 0},
        }
    )
    assert "structural" not in result["pattern"]
    assert "improved evidence sufficiency" in result["pattern"]


def test_parent_run_context_count_matches_source_bodies():
    from ragvidence.data import load_dataset

    sources, questions = load_dataset(EXERCISE_ROOT)
    run = run_experiment(
        EXERCISE_ROOT,
        StrategyConfig(
            name="parents",
            strategy="bm25",
            child_splitter="recursive",
            child_size=80,
            child_overlap=10,
            k=2,
        ),
    )
    lengths = {source.source_unit_id: len(source.body) for source in sources}
    for query in run.queries:
        assert query.returned_context_characters == sum(
            lengths[item.source_unit_id] for item in query.hits
        )
    assert evaluate_run(run, questions, sources=sources)["manifest"]["warnings"]


def test_runner_composes_hybrid_children_variants_and_reranking(monkeypatch):
    import numpy as np

    from ragvidence import pipeline as experiment_pipeline
    from ragvidence import runner as experiment_runner
    from ragvidence.strategies.semantic import SemanticStrategy

    class Embeddings:
        model_name = "fake-semantic"

        def embed_documents(self, texts):
            return np.asarray([[1, len(text) / 100] for text in texts], dtype=np.float32)

        def embed_query(self, text):
            return np.asarray([1, 1], dtype=np.float32)

    class Reranker:
        def __init__(self, model_name, *, cache_dir=None):
            assert model_name == "fake-reranker"

        def rerank(self, query, hits, texts, *, k):
            # Runner must pass parent IDs and complete text, including for children.
            assert all(item.source_unit_id in texts for item in hits)
            assert all(item.metadata["returned_context"] == "full_parent" for item in hits)
            return [
                item.model_copy(update={"rank": index})
                for index, item in enumerate(reversed(hits), start=1)
            ][:k]

    monkeypatch.setattr(
        experiment_pipeline,
        "semantic_strategy",
        lambda config, cache_dir, settings: SemanticStrategy(provider=Embeddings()),
    )
    monkeypatch.setattr(experiment_runner, "FastEmbedReranker", Reranker)
    run = run_experiment(
        EXERCISE_ROOT,
        StrategyConfig(
            name="composed",
            strategy="hybrid",
            representation="heading_context",
            child_splitter="recursive",
            child_size=90,
            child_overlap=10,
            query_variants={"DEV-01": ["pairing reset duration"]},
            reranker_model="fake-reranker",
            candidate_k=20,
            k=2,
        ),
    )
    assert len(run.queries[0].search_queries) == 2
    assert all(len(query.hits) == 2 for query in run.queries)
    assert all([item.rank for item in query.hits] == [1, 2] for query in run.queries)


def test_effective_embedding_defaults_are_recorded(monkeypatch):
    from ragvidence import runner as experiment_runner

    monkeypatch.setenv("RAGVIDENCE_EMBEDDING_MODEL", "configured-model")
    monkeypatch.setenv("RAGVIDENCE_EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setattr(
        experiment_runner, "build_strategy", lambda config, cache_dir, settings: FixedStrategy([])
    )
    run = run_experiment(EXERCISE_ROOT, StrategyConfig(name="effective", strategy="semantic"))
    assert run.manifest.config.model == "configured-model"
    assert run.manifest.config.provider == "ollama"


@pytest.mark.parametrize("options", [["--strategies", ""], ["--k", "0"], ["--provider", "invalid"]])
def test_benchmark_invalid_options_have_actionable_errors(tmp_path, options):
    result = CliRunner().invoke(app, ["benchmark", str(tmp_path), *options])
    assert result.exit_code == 2
    assert "Traceback" not in result.output


def test_new_pipeline_config_and_warnings_are_visible_in_reports():
    from ragvidence.data import load_dataset
    from ragvidence.reporting.html import render_html
    from ragvidence.reporting.markdown import render_markdown
    from ragvidence.reporting.payload import build_report

    sources, questions = load_dataset(EXERCISE_ROOT)
    run = run_experiment(
        EXERCISE_ROOT,
        StrategyConfig(
            name="report",
            strategy="bm25",
            child_splitter="recursive",
            child_size=80,
            child_overlap=10,
        ),
    )
    report = build_report(evaluate_run(run, questions, sources=sources))
    template = Path(__file__).parents[2] / "src/ragvidence/reporting/templates/report.html.j2"
    for content in [render_html(report, template), render_markdown(report)]:
        assert "child_splitter" in content
        assert "candidate_k" in content
        assert "full parent source units" in content
