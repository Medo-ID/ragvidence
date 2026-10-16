import json
import sys
from types import ModuleType

import numpy as np
import pytest
from typer.testing import CliRunner

from ragvidence import pipeline, portable_config
from ragvidence.capabilities import CAPABILITIES
from ragvidence.cli import app
from ragvidence.ingestion import load_corpus
from ragvidence.models import StrategyConfig
from ragvidence.portable import run_portable
from ragvidence.strategies.semantic import SemanticStrategy


@pytest.fixture
def fake_models(monkeypatch):
    observed = []

    class Embeddings:
        model_name = "contract-fixture"

        def embed_documents(self, texts):
            observed.extend(texts)
            return np.asarray(
                [[1.0, float("power" in text), float("reset" in text)] for text in texts]
            )

        def embed_query(self, text):
            observed.append(text)
            return np.asarray([1.0, float("power" in text), float("reset" in text)])

    monkeypatch.setattr(
        pipeline,
        "semantic_strategy",
        lambda config, cache_dir, settings: SemanticStrategy(provider=Embeddings()),
    )
    module = ModuleType("fastembed.rerank.cross_encoder")

    class Encoder:
        def __init__(self, model_name, **kwargs):
            assert model_name == "fixture-reranker"

        def rerank(self, query, documents):
            observed.extend([query, *documents])
            return [float("reset" in text) + 0.1 for text in documents]

    module.TextCrossEncoder = Encoder
    monkeypatch.setitem(sys.modules, "fastembed.rerank.cross_encoder", module)
    from ragvidence.providers.remote import ChatProvider

    def answer(self, system, user):
        observed.extend([system, user])
        return json.dumps({"queries": [json.loads(user)["question"]]})

    monkeypatch.setattr(ChatProvider, "answer", answer)
    return observed


def reference_file(tmp_path, snapshot, quote="eight seconds"):
    original = next(document for document in snapshot.documents if quote in document.body)
    start = original.body.index(quote)
    labels = tmp_path / "reviewed.json"
    labels.write_text(
        json.dumps(
            {
                "corpus_hash": snapshot.corpus_hash,
                "evidence": [
                    {
                        "evidence_id": "E",
                        "spans": [
                            {
                                "source_id": original.source_unit_id,
                                "start": start,
                                "end": start + len(quote),
                                "text": quote,
                            }
                        ],
                    }
                ],
                "questions": [
                    {
                        "question_id": "Q",
                        "question": "reset",
                        "split": "dev",
                        "answerable": True,
                        "required_evidence_ids": ["E"],
                        "reference_answer": "GOLDSECRET",
                    }
                ],
            }
        )
    )
    return labels


@pytest.mark.parametrize(
    "command", [item.name for item in CAPABILITIES if item.name != "import-data"]
)
def test_each_portable_technique_uses_shared_snapshot_reports_and_traces(
    tmp_path, monkeypatch, fake_models, command
):
    monkeypatch.setattr(portable_config, "user_config_path", lambda: tmp_path / "no-user.toml")
    source = tmp_path / "manual.md"
    source.write_text("# Device\nReset for eight seconds.\n\nUse USB-C power.")
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    variants = tmp_path / "variants.json"
    variants.write_text('{"Q":["reset procedure","reset procedure"]}')
    prefixes = tmp_path / "prefixes.json"
    prefixes.write_text(
        json.dumps(
            {
                document.source_unit_id: {
                    "text_hash": document.metadata["text_hash"],
                    "prefix": "Device reset instructions",
                }
                for document in snapshot.documents
            }
        )
    )
    args = [
        command,
        str(source),
        "--reviewed",
        str(labels),
        "--format",
        "json",
        "--format",
        "html",
        "--format",
        "markdown",
        "--output",
        str(tmp_path / "out"),
        "--no-input",
    ]
    if command == "multi-query":
        args.extend(["--variants", str(variants)])
    if command == "contextual":
        args.extend(["--prefixes", str(prefixes)])
    if command == "rerank":
        args.extend(["--reranker-model", "fixture-reranker"])
    if command == "metadata-filter":
        filters = tmp_path / "filters.json"
        filters.write_text('{"all":[{"field":"format","op":"eq","value":".md"}]}')
        args.extend(["--filters", str(filters)])
    if command in {"rewrite", "auto-multi-query"}:
        args.extend(["--rewrite-model", "fixture-rewriter"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    root = next((tmp_path / "out").iterdir())
    run = json.loads((root / "run.json").read_text())
    report = json.loads((root / "report.json").read_text())
    assert report["evaluation_level"] == "reviewed_evaluation"
    assert report["manifest"]["corpus_hash"] == snapshot.corpus_hash
    assert report["questions"][0]["stages"] == run["queries"][0]["stages"]
    assert run["queries"][0]["context_hash"] == report["questions"][0]["context_hash"]
    assert report["questions"][0]["metrics"]["sufficient_evidence"] is True
    assert "GOLDSECRET" not in " ".join(fake_models)
    names = [stage["name"] for stage in run["queries"][0]["stages"]]
    assert names[-1] == "context_selection"
    if command == "hybrid":
        assert names[:3] == ["lexical", "dense", "hybrid_fusion"]
    if command == "parent-child":
        assert "parent_expansion" in names
    if command == "rerank":
        assert "reranking" in names
    if command == "multi-query":
        assert run["queries"][0]["search_queries"] == ["reset", "reset procedure"]
        assert "multi_query_fusion" in names


def test_parent_context_passes_when_matching_child_is_insufficient(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("reset button\n\nHold for eight seconds.")
    snapshot = load_corpus(source, exclude=[], size=12, overlap=0)
    labels = reference_file(tmp_path, snapshot)

    def execute(config):
        return run_portable(
            source,
            [],
            config,
            output_root=tmp_path / "out",
            chunk_size=12,
            chunk_overlap=0,
            reviewed_file=labels,
        ).report

    child = execute(StrategyConfig(name="child", strategy="bm25", k=1))
    parent = execute(
        StrategyConfig(
            name="parent",
            strategy="bm25",
            k=1,
            child_splitter="recursive",
            child_size=12,
            child_overlap=0,
            child_k=1,
        )
    )
    assert child["questions"][0]["metrics"]["sufficient_evidence"] is False
    assert parent["questions"][0]["metrics"]["sufficient_evidence"] is True
    assert parent["questions"][0]["hits"][0]["text"] == source.read_bytes().decode("utf-8")
    assert (
        parent["questions"][0]["context_characters"] > child["questions"][0]["context_characters"]
    )


def test_nested_hybrid_and_multiquery_trace_keeps_all_branch_contributions(tmp_path, fake_models):
    from ragvidence.models import SearchQuestion

    source = tmp_path / "manual.txt"
    source.write_text("Reset power instructions")
    report = run_portable(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        StrategyConfig(
            name="nested",
            strategy="hybrid",
            query_variants={"Q": ["power"]},
            k=1,
            branch_k=2,
            query_k=3,
        ),
        output_root=tmp_path / "out",
    ).report
    hit = report["questions"][0]["hits"][0]
    outer = hit["metadata"]["rrf_contributions"]
    assert len(outer) == 2
    assert all(len(item["metadata"]["rrf_contributions"]) == 2 for item in outer)
    branches = [
        stage for stage in report["questions"][0]["stages"] if stage["name"] in {"lexical", "dense"}
    ]
    assert len(branches) == 4
    assert all(stage["details"]["limit"] == 2 for stage in branches)


@pytest.mark.parametrize(
    "command,args,reason",
    [
        ("rerank", [], "--reranker-model"),
        ("contextual", [], "--prefixes"),
        ("multi-query", [], "--variants"),
        ("bm25", ["--provider", "wrong"], "provider"),
        ("import-data", [], "--results"),
    ],
)
def test_missing_prerequisites_fail_without_traceback(tmp_path, command, args, reason):
    source = tmp_path / "manual.txt"
    source.write_text("Reset instructions")
    result = CliRunner().invoke(
        app,
        [
            command,
            str(source),
            "--query",
            "reset",
            "--no-input",
            "--output",
            str(tmp_path / "out"),
            *args,
        ],
    )
    assert result.exit_code != 0
    assert reason in result.output and "Traceback" not in result.output


def test_catalog_is_machine_readable_and_matches_registered_commands():
    result = CliRunner().invoke(app, ["techniques", "--format", "json"])
    assert result.exit_code == 0, result.output
    entries = json.loads(result.output)
    for entry in entries:
        assert CliRunner().invoke(app, [entry["name"], "--help"]).exit_code == 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda item: item.update(text="forged"),
        lambda item: item.update(end=item["end"] + 1),
        lambda item: item.update(source_id="unknown"),
        lambda item: item.update(score=float("nan")),
        lambda item: item.update(rank=True),
    ],
)
def test_imported_context_and_truncated_tails_are_validated(tmp_path, mutation):
    source = tmp_path / "manual.txt"
    source.write_text("Reset instructions")
    snapshot = load_corpus(source, exclude=[])
    hit = {"source_id": snapshot.documents[0].source_unit_id, "start": 0, "end": 5, "text": "Reset"}
    invalid = {**hit, "start": 6, "end": 18, "text": "instructions"}
    mutation(invalid)
    results = tmp_path / "results.jsonl"
    results.write_text(json.dumps({"question_id": "query-1", "hits": [hit, invalid]}))
    result = CliRunner().invoke(
        app,
        [
            "import-data",
            str(source),
            "--results",
            str(results),
            "--query",
            "reset",
            "--k",
            "1",
            "--no-input",
            "--output",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code != 0, result.output
    assert "Traceback" not in result.output


def test_native_exact_import_and_id_proxy_score_equivalent_spans_with_disclosed_scope(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Reset for eight seconds.")
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    native = run_portable(
        source,
        [],
        StrategyConfig(name="native", strategy="bm25", k=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    ).report
    for proxy in (False, True):
        document = snapshot.documents[0]
        hit = (
            {"source_unit_id": document.source_unit_id}
            if proxy
            else {
                "source_id": document.source_unit_id,
                "start": 0,
                "end": len(document.body),
                "text": document.body,
            }
        )
        results = tmp_path / "results.jsonl"
        results.write_text(json.dumps({"question_id": "Q", "hits": [hit]}))
        result = run_portable(
            source,
            [],
            StrategyConfig(name="import", strategy="imported", k=1),
            output_root=tmp_path / "out",
            reviewed_file=labels,
            results_file=results,
            formats=["html", "markdown"],
        )
        assert result.report["questions"][0]["metrics"] == native["questions"][0]["metrics"]
        assert result.report["questions"][0]["query_time_ms"] is None
        assert result.report["manifest"]["index_time_ms"] is None
        assert result.report["evaluation"]["scope"] == (
            "registered_unit_proxy" if proxy else "exact_returned_spans"
        )
        assert "Timing unavailable" in (result.directory / "report.html").read_text()
        if proxy:
            assert "registered-unit proxies" in " ".join(result.report["observations"])


def test_misleading_context_prefix_can_regress_and_never_becomes_gold(tmp_path, fake_models):
    source = tmp_path / "documents.json"
    source.write_text(
        json.dumps([{"text": "Reset for eight seconds."}, {"text": "Warranty details."}])
    )
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    baseline = run_portable(
        source,
        [],
        StrategyConfig(name="dense", strategy="semantic", k=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    ).report
    prefixes = tmp_path / "prefixes.json"
    prefixes.write_text(
        json.dumps(
            {
                doc.source_unit_id: {
                    "text_hash": doc.metadata["text_hash"],
                    "prefix": "power" if index == 0 else "reset eight seconds",
                }
                for index, doc in enumerate(snapshot.documents)
            }
        )
    )
    changed = run_portable(
        source,
        [],
        StrategyConfig(name="contextual", strategy="semantic", representation="contextual", k=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
        prefixes_file=prefixes,
    )
    assert baseline["questions"][0]["metrics"]["sufficient_evidence"] is True
    assert changed.report["questions"][0]["metrics"]["sufficient_evidence"] is False
    assert changed.report["questions"][0]["hits"][0]["text"] == "Warranty details."
    frozen = json.loads((changed.directory / "search-sources.json").read_text())
    assert frozen[1]["metadata"]["context_prefix"] == "reset eight seconds"


def test_context_budget_loss_is_reflected_in_reviewed_evidence(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Reset for eight seconds.")
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    result = run_portable(
        source,
        [],
        StrategyConfig(name="budget", strategy="bm25", k=1, context_budget=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    question = result.report["questions"][0]
    assert question["hits"] == [] and question["metrics"]["sufficient_evidence"] is False
    assert question["metrics"]["missing_evidence_ids"] == ["E"]
    assert question["context_measurement"]["skipped"]


def test_shared_reviewed_spans_remain_valid_across_chunk_size_and_overlap(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Reset for eight seconds. Then release the button.")
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    for size, overlap in ((10, 0), (10, 5), (500, 50)):
        result = run_portable(
            source,
            [],
            StrategyConfig(name="chunks", strategy="bm25", k=30),
            output_root=tmp_path / "out",
            reviewed_file=labels,
            chunk_size=size,
            chunk_overlap=overlap,
        )
        assert result.report["manifest"]["corpus_hash"] == snapshot.corpus_hash
        assert result.report["questions"][0]["metrics"]["evidence_coverage"] == 1


@pytest.mark.parametrize(
    "command,extra",
    [("semantic", []), ("hybrid", []), ("rerank", ["--reranker-model", "not-loaded"])],
)
def test_source_only_commands_do_not_construct_models(tmp_path, monkeypatch, command, extra):
    from ragvidence import runner

    monkeypatch.setattr(
        runner, "build_strategy", lambda *args: pytest.fail("Source-only must not load a model")
    )
    source = tmp_path / "manual.txt"
    source.write_text("Reset instructions")
    result = CliRunner().invoke(
        app, [command, str(source), "--no-input", "--output", str(tmp_path / "out"), *extra]
    )
    assert result.exit_code == 0, result.output
    assert "ingestion_only" in result.output


@pytest.mark.parametrize("helpful", [True, False])
def test_supplied_variants_can_help_or_regress_without_changing_original_question(
    tmp_path, helpful
):
    records = [
        {"text": "Power connector cable instructions."},
        {"text": "Reset pairing for eight seconds."},
    ]
    if not helpful:
        records.reverse()
    source = tmp_path / "documents.json"
    source.write_text(json.dumps(records))
    snapshot = load_corpus(source, exclude=[])
    labels = reference_file(tmp_path, snapshot)
    values = json.loads(labels.read_text())
    values["questions"][0]["question"] = "How do I pair my earpieces?" if helpful else "reset"
    labels.write_text(json.dumps(values))
    baseline = run_portable(
        source,
        [],
        StrategyConfig(name="baseline", strategy="bm25", k=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    variants = (
        ["reset pairing duration", "eight seconds reset"]
        if helpful
        else ["power connector", "power cable"]
    )
    changed = run_portable(
        source,
        [],
        StrategyConfig(name="variants", strategy="bm25", k=1, query_variants={"Q": variants}),
        output_root=tmp_path / "out",
        reviewed_file=labels,
    )
    assert baseline.report["questions"][0]["metrics"]["sufficient_evidence"] is (not helpful)
    assert changed.report["questions"][0]["metrics"]["sufficient_evidence"] is helpful
    assert changed.report["questions"][0]["question"] == baseline.report["questions"][0]["question"]


@pytest.mark.parametrize("query", ["reset", "unknown-vocabulary", "!!!"])
def test_bm25_ties_are_stable_in_frozen_source_order(query):
    from ragvidence.models import SourceUnit
    from ragvidence.representation import build_records
    from ragvidence.strategies.bm25 import BM25Strategy

    strategy = BM25Strategy()
    sources = [
        SourceUnit(source_unit_id=name, document_id=name, body="reset button")
        for name in ("A", "B", "C")
    ]
    strategy.index(build_records(sources, "body"))
    assert [hit.source_unit_id for hit in strategy.search(query, k=2)] == ["A", "B"]
