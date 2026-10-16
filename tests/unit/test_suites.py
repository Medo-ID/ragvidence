import json
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from ragvidence import portable, portable_config
from ragvidence.cli import app
from ragvidence.config import Settings
from ragvidence.evaluation.aggregation import paired_interval
from ragvidence.ingestion import load_corpus
from ragvidence.models import SearchQuestion
from ragvidence.portable_config import PortableOptions
from ragvidence.suites import preparation
from ragvidence.suites.execution import compare_data
from ragvidence.suites.models import Criteria, Pricing, SuiteSpec
from ragvidence.suites.report import criterion_matches
from ragvidence.suites.resources import measured, supplied_cost
from ragvidence.suites.storage import read_json, seal_attempt


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    monkeypatch.setattr(portable_config, "user_config_path", lambda: tmp_path / "no-config.toml")
    source = tmp_path / "manual.md"
    source.write_text(
        "# Reset\n\nreset button\n\nHold for eight seconds.\n\n"
        "# Power\n\npower instructions\n\nUse USB-C supply.\n\n"
        "# Warranty\n\nwarranty terms\n\nCovered for two years.\n"
    )
    snapshot = load_corpus(source, exclude=[])
    original = snapshot.documents[0]
    evidence = []
    for name, quote in (("RESET", "eight seconds"), ("POWER", "USB-C"), ("WARRANTY", "two years")):
        start = original.body.index(quote)
        evidence.append(
            {
                "evidence_id": name,
                "spans": [
                    {
                        "source_id": original.source_unit_id,
                        "start": start,
                        "end": start + len(quote),
                        "text": quote,
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
                        "question_id": "Q1",
                        "question": "reset",
                        "split": "dev",
                        "answerable": True,
                        "required_evidence_ids": ["RESET"],
                        "tags": ["family:device", "reset"],
                    },
                    {
                        "question_id": "Q2",
                        "question": "power",
                        "split": "dev",
                        "answerable": True,
                        "required_evidence_ids": ["POWER"],
                        "tags": ["family:device"],
                    },
                    {
                        "question_id": "Q3",
                        "question": "warranty",
                        "split": "heldout",
                        "answerable": True,
                        "required_evidence_ids": ["WARRANTY"],
                    },
                    {
                        "question_id": "U",
                        "question": "battery capacity",
                        "split": "dev",
                        "answerable": False,
                    },
                ],
            }
        )
    )
    return source, labels


def options(tmp_path, **values):
    return PortableOptions(
        output=tmp_path / "reports",
        cache_dir=tmp_path / "cache",
        formats=["html", "json", "markdown"],
        **values,
    )


def spec(**values):
    return SuiteSpec.model_validate(
        {
            "variants": [
                {"name": "body", "technique": "bm25"},
                {"name": "parents", "technique": "parent-child"},
            ],
            "bootstrap_samples": 100,
            **values,
        }
    )


def run(tmp_path, corpus, **kwargs):
    source, labels = corpus
    return compare_data(
        source,
        [],
        options(tmp_path, k=1, chunk_size=12, chunk_overlap=0),
        spec(),
        Settings(_env_file=None),
        reviewed_file=labels,
        **kwargs,
    )


def test_suite_freezes_once_shares_originals_and_reconciles_all_exports(
    tmp_path, corpus, monkeypatch
):
    loads = []
    original = preparation.load_corpus

    def observed(*args, **kwargs):
        loads.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(preparation, "load_corpus", observed)
    result = run(tmp_path, corpus)
    assert len(loads) == 1
    report = result.report
    assert report["state"] == "complete" and report["phase"] == "dev"
    assert report["evaluation_level"] == "reviewed_comparison"
    assert {entry["report"]["manifest"]["corpus_hash"] for entry in report["participants"]} == {
        json.loads(corpus[1].read_text())["corpus_hash"]
    }
    pair = report["comparisons"][0]
    assert pair["quality_comparable"] is True
    assert pair["splits"]["dev"]["all"]["changes"]["improved"] == 2
    interval = pair["splits"]["dev"]["all"]["intervals"]["sufficiency_rate"]
    assert interval["estimate"] == 1 and interval["group_count"] == 1 and interval["lower"] is None
    assert pair["splits"]["heldout"]["all"]["answerable_questions"] == 0
    assert all(
        q["question_id"] != "Q3"
        for entry in report["participants"]
        for q in entry["report"]["questions"]
    )
    assert read_json(result.exports["json"]) == report
    for format in ("html", "markdown"):
        text = result.exports[format].read_text()
        assert "parents" in text and "eight seconds" in text and "heldout" in text
    assert (result.directory / "shortlist.json").is_file()


def test_unlabeled_comparison_has_no_quality_winner_or_invented_cost(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Reset with the button")
    result = compare_data(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        options(tmp_path),
        spec(),
        Settings(_env_file=None),
    )
    assert result.report["evaluation_level"] == "unscored_comparison"
    assert all(
        not entry["summaries"] and entry["usage"]["cost"] is None
        for entry in result.report["participants"]
    )
    assert result.report["comparisons"][0]["quality_comparable"] is False
    assert "cannot establish a quality winner" in " ".join(result.report["observations"])


def test_resume_uses_frozen_data_and_validates_completed_results_without_rerunning(
    tmp_path, corpus, monkeypatch
):
    result = run(tmp_path, corpus)
    old_export = result.exports["html"].read_bytes()
    corpus[0].unlink()
    corpus[1].unlink()
    monkeypatch.setattr(
        portable,
        "execute_retrieval",
        lambda *args, **kwargs: pytest.fail("Completed trial must be reused"),
    )
    resumed = compare_data(
        Path("missing-source"),
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        resume=result.directory,
    )
    assert resumed.report["resumed"] is True
    assert all(entry["trials"][0]["reused"] for entry in resumed.report["participants"])
    assert result.exports["html"].read_bytes() == old_export
    assert resumed.exports["html"] != result.exports["html"]


@pytest.mark.parametrize("target", ["run.json", "report.json", "snapshot.json"])
def test_resume_rejects_modified_artifacts(tmp_path, corpus, target):
    result = run(tmp_path, corpus)
    path = (
        result.directory / target
        if target == "snapshot.json"
        else next(result.directory.glob("jobs/body/trial-0/*/" + target))
    )
    value = read_json(path)
    value["changed"] = True
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="changed|mismatch|validation"):
        compare_data(
            Path("unused"),
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            resume=result.directory,
        )


def test_resealed_but_forged_report_metrics_are_recomputed_on_resume(tmp_path, corpus):
    result = run(tmp_path, corpus)
    directory = next(result.directory.glob("jobs/body/trial-0/*"))
    value = read_json(directory / "report.json")
    value["questions"][0]["metrics"]["sufficient_evidence"] = True
    (directory / "report.json").write_text(json.dumps(value))
    (directory / "checkpoint.json").unlink()
    seal_attempt(directory)
    with pytest.raises(ValueError, match="facts"):
        compare_data(
            Path("unused"),
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            resume=result.directory,
        )


def test_partial_failures_are_reported_and_resume_only_retries_failed_jobs(
    tmp_path, corpus, monkeypatch
):
    original = portable.execute_retrieval
    calls = []
    fail = True

    def execute(sources, questions, config, **kwargs):
        calls.append(config.name)
        if fail and config.name == "parents":
            raise RuntimeError("Temporary provider failure")
        return original(sources, questions, config, **kwargs)

    monkeypatch.setattr(portable, "execute_retrieval", execute)
    first = run(tmp_path, corpus)
    assert first.report["state"] == "partial_failure"
    assert first.report["participants"][1]["state"] == "failed"
    fail = False
    calls.clear()
    resumed = compare_data(
        corpus[0],
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        resume=first.directory,
    )
    assert resumed.report["state"] == "complete" and calls == ["parents"]
    assert len(list(first.directory.glob("jobs/parents/trial-0/*/status.json"))) == 2


def test_frozen_dev_shortlist_controls_heldout_and_records_local_reuse(tmp_path, corpus):
    dev = run(tmp_path, corpus)
    for count in (1, 2):
        heldout = compare_data(
            corpus[0],
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            phase="heldout",
            shortlist=dev.directory / "shortlist.json",
        )
        assert heldout.report["heldout_use"]["evaluation_number"] == count
        assert heldout.report["heldout_use"]["reused"] is (count > 1)
        assert all(
            [q["question_id"] for q in entry["report"]["questions"]] == ["Q3"]
            for entry in heldout.report["participants"]
        )
    with pytest.raises(ValueError, match="shortlist"):
        run(tmp_path, corpus, phase="heldout")


def test_grid_is_bounded_and_slices_include_empty_denominators(tmp_path, corpus):
    definition = spec(
        variants=[],
        grids=[
            {
                "variant": {"name": "chunks", "technique": "bm25"},
                "axes": {"chunk_size": [12, 40], "chunk_overlap": [0]},
            }
        ],
        slices={"reset": ["reset"], "absent": ["not-present"]},
    )
    result = compare_data(
        corpus[0],
        [],
        options(tmp_path, k=2),
        definition,
        Settings(_env_file=None),
        reviewed_file=corpus[1],
    )
    assert len(result.report["participants"]) == 2
    empty = result.report["participants"][0]["summaries"]["dev"]["absent"]
    assert empty["answerable_questions"] == 0 and empty["sufficiency_rate"] is None
    definition.max_configurations = 1
    with pytest.raises(ValueError, match="configurations"):
        definition.expanded()


def test_fixed_depth_and_query_budget_preflight_fail_before_execution(
    tmp_path, corpus, monkeypatch
):
    monkeypatch.setattr(
        portable,
        "execute_retrieval",
        lambda *args, **kwargs: pytest.fail("Preflight must reject first"),
    )
    definition = spec(
        variants=[
            {"name": "one", "technique": "bm25", "options": {"k": 1}},
            {"name": "two", "technique": "bm25", "options": {"k": 2}},
        ]
    )
    with pytest.raises(ValueError, match="same final k"):
        compare_data(
            corpus[0],
            [],
            options(tmp_path),
            definition,
            Settings(_env_file=None),
            reviewed_file=corpus[1],
        )
    with pytest.raises(ValueError, match="max_query_calls"):
        compare_data(
            corpus[0],
            [],
            options(tmp_path),
            spec(max_query_calls=1),
            Settings(_env_file=None),
            reviewed_file=corpus[1],
        )


def test_vector_cache_compatibility_and_warm_trials_do_not_inflate_question_counts(
    tmp_path, corpus, monkeypatch
):
    from ragvidence import pipeline
    from ragvidence.strategies.semantic import SemanticStrategy

    embedded = []

    class Provider:
        def __init__(self, name):
            self.model_name = name

        def embed_documents(self, texts):
            embedded.append(self.model_name)
            return np.asarray([[1.0, len(text)] for text in texts])

        def embed_query(self, text):
            return np.asarray([1.0, 1.0])

    monkeypatch.setattr(
        pipeline,
        "semantic_strategy",
        lambda config, cache_dir, settings: SemanticStrategy(
            provider=Provider(config.model), cache_dir=cache_dir / "embeddings"
        ),
    )
    definition = spec(
        warm_repeats=1,
        variants=[
            {"name": name, "technique": "semantic", "options": {"model": model}}
            for name, model in (("a", "model-A"), ("a-repeat", "model-A"), ("b", "model-B"))
        ],
    )
    result = compare_data(
        corpus[0],
        [],
        options(tmp_path),
        definition,
        Settings(_env_file=None),
        reviewed_file=corpus[1],
    )
    assert embedded == ["model-A", "model-B"]
    first = result.report["participants"][0]
    assert [trial["resources"]["vector_cache"] for trial in first["trials"]] == [
        "cold_vectors",
        "warm_vectors",
    ]
    assert first["summaries"]["dev"]["all"]["answerable_questions"] == 2


def test_cli_compares_own_folder_excludes_questions_and_returns_partial_failure_code(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "manual.txt").write_text("Reset the button")
    questions = folder / "questions.txt"
    questions.write_text("reset\n")
    result = CliRunner().invoke(
        app,
        [
            "compare-data",
            str(folder),
            "--techniques",
            "bm25,heading-context",
            "--questions",
            str(questions),
            "--output",
            str(tmp_path / "out"),
            "--format",
            "json",
            "--no-input",
        ],
    )
    assert result.exit_code == 1, result.output
    exported = next((tmp_path / "out").glob("*/exports/*/report.json"))
    report = read_json(exported)
    assert report["state"] == "partial_failure"
    assert report["participants"][0]["report"]["input"]["file_count"] == 1
    assert report["participants"][1]["state"] == "failed"
    assert "Traceback" not in result.output


def test_paired_cluster_intervals_match_hand_calculated_examples():
    interval = paired_interval([0.0, 1.0], ["a", "b"], seed=12, samples=1000)
    assert interval["estimate"] == 0.5 and interval["lower"] == 0 and interval["upper"] == 1
    assert interval == paired_interval([0.0, 1.0], ["a", "b"], seed=12, samples=1000)
    grouped = paired_interval([1.0, 1.0, 0.0], ["a", "a", "b"], seed=1, samples=1000)
    assert grouped["estimate"] == pytest.approx(2 / 3) and grouped["group_count"] == 2
    assert paired_interval([1.0, 0.0], ["same", "same"], seed=1, samples=100)["lower"] is None
    assert paired_interval([], [], seed=1, samples=100)["estimate"] is None


def test_missing_resources_and_supplied_pricing_remain_explicit(tmp_path):
    resources = {"query_ms": measured([None, 10]), "context_units": measured([30, 40])}
    criteria = criterion_matches(
        None,
        resources,
        Criteria(max_mean_query_ms=15),
    )
    assert criteria["status"] == "unknown"
    usage = tmp_path / "usage.json"
    usage.write_text(
        json.dumps(
            [
                {
                    "question_id": "Q",
                    "model_id": "provider:model",
                    "input_tokens": 1000,
                    "output_tokens": 500,
                }
            ]
        )
    )
    pricing = Pricing(
        identity="test-rates",
        currency="USD",
        rates={"provider:model": {"input_per_million": 2, "output_per_million": 4}},
    )
    estimate = supplied_cost(usage, pricing, {"Q"})
    assert estimate["cost"] == 0.004 and estimate["estimate"] is True
    assert supplied_cost(usage, None, {"Q"})["cost"] is None
    assert supplied_cost(None, pricing, {"Q"})["input_tokens"] is None


@pytest.mark.parametrize("proxy", [False, True])
def test_imported_baseline_keeps_missing_timing_and_proxy_scope_and_all_phase_records(
    tmp_path, corpus, proxy
):
    source, labels = corpus
    snapshot = load_corpus(source, exclude=[])
    original = snapshot.documents[0]
    hit = (
        {"source_unit_id": original.source_unit_id}
        if proxy
        else {
            "source_id": original.source_unit_id,
            "start": 0,
            "end": len(original.body),
            "text": original.body,
        }
    )
    records = [
        {"question_id": question["question_id"], "hits": [hit]}
        for question in read_json(labels)["questions"]
    ]
    results = tmp_path / "baseline.jsonl"
    results.write_text("\n".join(json.dumps(record) for record in records))
    definition = spec(
        variants=[
            {"name": "existing", "technique": "import-data", "results_file": str(results)},
            {"name": "body", "technique": "bm25"},
        ]
    )
    dev = compare_data(
        source,
        [],
        options(tmp_path, k=1, chunk_size=12, chunk_overlap=0),
        definition,
        Settings(_env_file=None),
        reviewed_file=labels,
    )
    baseline = dev.report["participants"][0]
    assert baseline["resources"]["query_ms"] == {
        "mean_known": None,
        "known_count": 0,
        "missing_count": 3,
    }
    assert baseline["resources"]["index_ms"] is None
    pair = dev.report["comparisons"][0]
    assert pair["quality_comparable"] is (not proxy)
    assert pair["splits"]["dev"]["all"]["changes"]["regressed"] == 2
    heldout = compare_data(
        source,
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        phase="heldout",
        shortlist=dev.directory / "shortlist.json",
    )
    assert heldout.report["participants"][0]["report"]["questions"][0]["question_id"] == "Q3"


def test_exact_token_budget_is_shared_across_different_final_depths_and_frozen_on_resume(
    tmp_path, corpus
):
    tokenizers = pytest.importorskip("tokenizers")
    tokenizer = tokenizers.Tokenizer(tokenizers.models.WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.Whitespace()
    path = tmp_path / "tokenizer.json"
    path.write_text(tokenizer.to_str())
    definition = spec(
        policy="fixed_tokens",
        variants=[
            {"name": "one", "technique": "bm25", "options": {"k": 1}},
            {"name": "two", "technique": "parent-child", "options": {"k": 2}},
        ],
    )
    result = compare_data(
        corpus[0],
        [],
        options(tmp_path, tokenizer_file=path, context_budget=200),
        definition,
        Settings(_env_file=None),
        reviewed_file=corpus[1],
    )
    assert {entry["resources"]["context_unit"] for entry in result.report["participants"]} == {
        "tokens"
    }
    path.unlink()
    resumed = compare_data(
        Path("missing"),
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        resume=result.directory,
    )
    assert resumed.report["state"] == "complete"
    definition.variants[1].options["context_budget"] = 201
    with pytest.raises(ValueError, match="same budget"):
        compare_data(
            corpus[0],
            [],
            options(
                tmp_path,
                tokenizer_file=next(result.directory.glob("inputs/*.json")),
                context_budget=200,
            ),
            definition,
            Settings(_env_file=None),
            reviewed_file=corpus[1],
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"variants": [{"name": "../escape", "technique": "bm25"}]},
        {"variants": [{"name": "x", "technique": "unknown"}]},
        {"variants": [{"name": "x", "technique": "bm25"}, {"name": "x", "technique": "bm25"}]},
        {"slices": {"all": ["tag"]}},
        {"max_configurations": 33},
        {"bootstrap_samples": 10},
        {"warm_repeats": 4},
        {"variants": [{"name": "x", "technique": "bm25"}], "baseline": "missing"},
    ],
)
def test_invalid_suite_definitions_are_rejected(changes):
    with pytest.raises(ValueError):
        spec(**changes).expanded()


def test_json_suite_paths_are_relative_and_cache_and_sidecars_are_excluded(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "manual.md").write_text("# Device\nReset the button")
    cache = folder / "custom-cache"
    cache.mkdir()
    (cache / "cached.txt").write_text("MUST NOT INDEX")
    (folder / "questions.txt").write_text("reset")
    suite = folder / "suite.json"
    suite.write_text(
        json.dumps(
            {
                "variants": [
                    {"name": "body", "technique": "bm25"},
                    {
                        "name": "variants",
                        "technique": "multi-query",
                        "variants_file": "variants.json",
                    },
                ]
            }
        )
    )
    from ragvidence.questions import load_questions

    question_id = load_questions([], folder / "questions.txt")[0].question_id
    (folder / "variants.json").write_text(json.dumps({question_id: ["button instructions"]}))
    result = CliRunner().invoke(
        app,
        [
            "compare-data",
            str(folder),
            "--suite",
            str(suite),
            "--questions",
            str(folder / "questions.txt"),
            "--cache-dir",
            str(cache),
            "--output",
            str(tmp_path / "out"),
            "--format",
            "json",
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    exported = next((tmp_path / "out").glob("*/exports/*/report.json"))
    assert all(
        entry["report"]["input"]["file_count"] == 1 for entry in read_json(exported)["participants"]
    )


def test_cli_resume_rejects_silent_option_changes(tmp_path, corpus):
    first = run(tmp_path, corpus)
    result = CliRunner().invoke(
        app, ["compare-data", "missing", "--resume", str(first.directory), "--k", "9", "--no-input"]
    )
    assert result.exit_code == 1 and "frozen options" in result.output


def test_shortlist_configuration_and_frozen_sidecar_changes_are_rejected(tmp_path, corpus):
    original = run(tmp_path, corpus)
    shortlist = original.directory / "shortlist.json"
    value = read_json(shortlist)
    value["jobs"][0]["chunk_size"] = 99
    shortlist.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="binding"):
        compare_data(
            corpus[0],
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            phase="heldout",
            shortlist=shortlist,
        )


def test_source_only_comparison_preserves_not_executed_status(tmp_path, monkeypatch):
    source = tmp_path / "manual.txt"
    source.write_text("Reset the device")
    from ragvidence import runner

    monkeypatch.setattr(
        runner, "build_strategy", lambda *args: pytest.fail("No questions means no retriever")
    )
    result = compare_data(source, [], options(tmp_path), spec(), Settings(_env_file=None))
    assert all(
        entry["report"]["evaluation_level"] == "ingestion_only"
        for entry in result.report["participants"]
    )
    assert all(
        entry["resources"]["query_ms"]["mean_known"] is None
        for entry in result.report["participants"]
    )


def test_criteria_use_split_measurements_and_explicit_counter_units(tmp_path, corpus):
    definition = spec(criteria={"max_mean_query_ms": 1e9})
    result = compare_data(
        corpus[0],
        [],
        options(tmp_path),
        definition,
        Settings(_env_file=None),
        reviewed_file=corpus[1],
    )
    for entry in result.report["participants"]:
        assert entry["criteria"]["dev"]["status"] == "matched"
        assert entry["criteria"]["heldout"]["status"] == "unknown"
    with pytest.raises(ValueError, match="context_unit"):
        Criteria(max_mean_context_units=500)
    status = criterion_matches(
        None,
        {"context_unit": "characters", "context_units": measured([100])},
        Criteria(max_mean_context_units=500, context_unit="tokens"),
    )
    assert status["status"] == "unknown"


def test_comparison_report_escapes_source_html_and_uses_self_contained_assets(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text('<script>alert("bad")</script> reset')
    result = compare_data(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        options(tmp_path),
        spec(),
        Settings(_env_file=None),
    )
    for format in ("html", "markdown"):
        content = result.exports[format].read_text()
        assert "<script>alert" not in content and "&lt;script&gt;" in content
    html = result.exports["html"].read_text()
    assert "data:font/woff2;base64," in html and "<script src=" not in html


def test_explicit_groups_and_family_tags_share_the_same_group_namespace(tmp_path, corpus):
    definition = spec(question_groups={"Q2": "device"})
    result = compare_data(
        corpus[0],
        [],
        options(tmp_path),
        definition,
        Settings(_env_file=None),
        reviewed_file=corpus[1],
    )
    interval = result.report["comparisons"][0]["splits"]["dev"]["all"]["intervals"][
        "sufficiency_rate"
    ]
    assert interval["question_count"] == 2 and interval["group_count"] == 1
    assert interval["lower"] is None
