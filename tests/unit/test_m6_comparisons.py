import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ragvidence import portable, portable_config
from ragvidence.artifacts import content_hash
from ragvidence.cli import app
from ragvidence.config import Settings
from ragvidence.models import StrategyConfig
from ragvidence.portable_config import PortableOptions
from ragvidence.providers.remote import ChatProvider
from ragvidence.suites.execution import compare_data
from ragvidence.suites.models import SuiteSpec
from ragvidence.suites.storage import read_json, seal_attempt


def options(tmp_path):
    return PortableOptions(
        output=tmp_path / "out",
        cache_dir=tmp_path / "cache",
        k=1,
        formats=["html", "markdown", "json"],
    )


def definition():
    return SuiteSpec.model_validate(
        {
            "bootstrap_samples": 100,
            "variants": [
                {"name": "baseline", "technique": "bm25"},
                {
                    "name": "scoped",
                    "technique": "metadata-filter",
                    "options": {
                        "filters": {
                            "all": [{"field": "record_metadata.version", "op": "eq", "value": 2}]
                        }
                    },
                },
                {
                    "name": "diverse",
                    "technique": "mmr",
                    "options": {"mmr": {"lambda_mult": 0.3, "candidates": 3}},
                },
                {
                    "name": "rewritten",
                    "technique": "rewrite",
                    "options": {
                        "rewrite": {"model": "fixture", "count": 1, "include_original": False}
                    },
                },
                {
                    "name": "compressed",
                    "technique": "compress",
                    "options": {
                        "filters": {
                            "all": [{"field": "record_metadata.version", "op": "eq", "value": 2}]
                        }
                    },
                },
            ],
        }
    )


def test_m6_comparison_shares_inputs_and_resumes_without_models_or_originals(
    tmp_path, m6_corpus, m6_embeddings, monkeypatch
):
    calls = []

    def answer(self, system, user):
        calls.append(user)
        return '{"queries":["reset eight seconds"]}'

    monkeypatch.setattr(ChatProvider, "answer", answer)
    path, labels, _ = m6_corpus
    result = compare_data(
        path, [], options(tmp_path), definition(), Settings(_env_file=None), reviewed_file=labels
    )
    report = result.report
    assert report["state"] == "complete" and len(calls) == 1
    participants = {entry["name"]: entry for entry in report["participants"]}
    assert (
        participants["scoped"]["report"]["questions"][0]["metrics"]["sufficient_evidence"] is True
    )
    assert participants["compressed"]["report"]["questions"][0]["metrics"][
        "missing_evidence_ids"
    ] == ["CONDITION"]
    assert read_json(result.exports["json"]) == report
    for format in ("html", "markdown"):
        text = result.exports[format].read_text()
        assert "query_rewriting" in text and "compression" in text and "mmr" in text
    path.unlink()
    labels.unlink()
    monkeypatch.setattr(
        portable,
        "execute_retrieval",
        lambda *a, **k: pytest.fail("Completed result must be validated and reused"),
    )
    resumed = compare_data(
        Path("unused"),
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        resume=result.directory,
    )
    assert resumed.report["state"] == "complete" and len(calls) == 1
    assert all(entry["trials"][0]["reused"] for entry in resumed.report["participants"])


def test_m6_call_bound_fails_before_any_model_and_counts_transformations(
    tmp_path, m6_corpus, monkeypatch
):
    monkeypatch.setattr(ChatProvider, "answer", lambda *a: pytest.fail("Must preflight"))
    spec = SuiteSpec.model_validate(
        {
            "max_query_calls": 7,
            "variants": [
                {
                    "name": "combo",
                    "technique": "hybrid",
                    "options": {
                        "rewrite": {"model": "fixture", "count": 2, "include_original": True},
                        "mmr": {},
                        "compression": {"mode": "model", "model": "fixture"},
                    },
                }
            ],
        }
    )
    # Per dev question: 3 queries*2 branches + rewrite + MMR + compression = 9.
    with pytest.raises(ValueError, match="max_query_calls"):
        compare_data(
            m6_corpus[0],
            [],
            options(tmp_path),
            spec,
            Settings(_env_file=None),
            reviewed_file=m6_corpus[1],
        )


def test_frozen_filters_apply_to_heldout_and_unknown_ids_fail(tmp_path, m6_corpus):
    predicate = [{"field": "record_metadata.version", "op": "eq", "value": 2}]
    spec = SuiteSpec.model_validate(
        {
            "variants": [
                {
                    "name": "scoped",
                    "technique": "metadata-filter",
                    "options": {"filters": {"questions": {"Q": predicate, "H": predicate}}},
                }
            ]
        }
    )
    dev = compare_data(
        m6_corpus[0],
        [],
        options(tmp_path),
        spec,
        Settings(_env_file=None),
        reviewed_file=m6_corpus[1],
    )
    heldout = compare_data(
        m6_corpus[0],
        [],
        options(tmp_path),
        SuiteSpec(),
        Settings(_env_file=None),
        phase="heldout",
        shortlist=dev.directory / "shortlist.json",
    )
    q = heldout.report["participants"][0]["report"]["questions"][0]
    assert q["question_id"] == "H" and q["metrics"]["sufficient_evidence"] is True
    spec.variants[0].options["filters"]["questions"]["unknown"] = predicate
    with pytest.raises(ValueError, match="unknown question"):
        compare_data(
            m6_corpus[0],
            [],
            options(tmp_path),
            spec,
            Settings(_env_file=None),
            reviewed_file=m6_corpus[1],
        )


def test_transformation_endpoint_change_is_rejected_on_resume(tmp_path, m6_corpus, monkeypatch):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: '{"queries":["reset"]}')
    spec = SuiteSpec.model_validate(
        {
            "variants": [
                {
                    "name": "rewritten",
                    "technique": "rewrite",
                    "options": {"rewrite": {"model": "fixture", "count": 1}},
                }
            ]
        }
    )
    result = compare_data(
        m6_corpus[0],
        [],
        options(tmp_path),
        spec,
        Settings(_env_file=None),
        reviewed_file=m6_corpus[1],
    )
    with pytest.raises(ValueError, match="endpoint changed"):
        compare_data(
            Path("unused"),
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None, transform_base_url="http://different.example"),
            resume=result.directory,
        )


def test_resealed_forged_compression_is_rejected_before_reuse(tmp_path, m6_corpus):
    spec = SuiteSpec.model_validate({"variants": [{"name": "compressed", "technique": "compress"}]})
    result = compare_data(
        m6_corpus[0],
        [],
        options(tmp_path),
        spec,
        Settings(_env_file=None),
        reviewed_file=m6_corpus[1],
    )
    directory = next(result.directory.glob("jobs/compressed/trial-0/*"))
    run = read_json(directory / "run.json")
    stage = next(stage for stage in run["queries"][0]["stages"] if stage["name"] == "compression")
    stage["details"]["selections"] = {}
    (directory / "run.json").write_text(json.dumps(run))
    (directory / "checkpoint.json").unlink()
    seal_attempt(directory)
    with pytest.raises(ValueError, match="compression selections"):
        compare_data(
            Path("unused"),
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            resume=result.directory,
        )


def test_cli_filters_sidecar_is_excluded_and_simple_comparison_keeps_baseline_plain(
    tmp_path, m6_corpus, monkeypatch
):
    monkeypatch.setattr(portable_config, "user_config_path", lambda: tmp_path / "no-user.toml")
    source, _, _ = m6_corpus
    filters = tmp_path / "filters.json"
    filters.write_text('{"all":[{"field":"record_metadata.version","op":"eq","value":2}]}')
    result = CliRunner().invoke(
        app,
        [
            "compare-data",
            str(source),
            "--query",
            "reset",
            "--techniques",
            "bm25,metadata-filter,compress",
            "--filters",
            str(filters),
            "--format",
            "json",
            "--output",
            str(tmp_path / "out"),
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    report = read_json(next((tmp_path / "out").glob("*/exports/*/report.json")))
    configs = {e["name"]: e["report"]["manifest"]["config"] for e in report["participants"]}
    assert "filters" not in configs["bm25"] and "compression" not in configs["bm25"]
    assert configs["metadata-filter"]["filters"]["all"][0]["value"] == 2
    assert configs["compress"]["compression"]["mode"] == "sentences"


def test_unused_m6_fields_preserve_old_configuration_hashes():
    config = StrategyConfig(name="old", strategy="bm25")
    values = config.model_dump()
    assert not {"filters", "mmr", "rewrite", "compression"} & values.keys()
    assert content_hash(values) == content_hash(config)


def test_resealed_forged_mmr_objective_is_rejected(tmp_path, m6_corpus, m6_embeddings):
    spec = SuiteSpec.model_validate({"variants": [{"name": "diverse", "technique": "mmr"}]})
    result = compare_data(
        m6_corpus[0],
        [],
        options(tmp_path),
        spec,
        Settings(_env_file=None),
        reviewed_file=m6_corpus[1],
    )
    directory = next(result.directory.glob("jobs/diverse/trial-0/*"))
    run = read_json(directory / "run.json")
    stage = next(stage for stage in run["queries"][0]["stages"] if stage["name"] == "mmr")
    stage["hits"][0]["metadata"]["mmr"]["objective"] = 999
    (directory / "run.json").write_text(json.dumps(run))
    (directory / "checkpoint.json").unlink()
    seal_attempt(directory)
    with pytest.raises(ValueError, match="MMR scores"):
        compare_data(
            Path("unused"),
            [],
            options(tmp_path),
            SuiteSpec(),
            Settings(_env_file=None),
            resume=result.directory,
        )
