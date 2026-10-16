import json

import pytest

from ragvidence.config import Settings
from ragvidence.models import RewriteConfig, SearchQuestion, StrategyConfig
from ragvidence.portable import run_portable
from ragvidence.providers.remote import ChatProvider
from ragvidence.transformations import rewrite_question


@pytest.mark.parametrize(
    "include,expected", [(True, ["original", "rephrased"]), (False, ["rephrased", "original"])]
)
def test_bounded_unique_queries_and_original_policy(monkeypatch, include, expected):
    calls = []

    def answer(self, system, user):
        calls.append(json.loads(user))
        assert "queries" in system
        return '{"queries":[" rephrased ","rephrased","original"]}'

    monkeypatch.setattr(ChatProvider, "answer", answer)
    config = RewriteConfig(model="fixture", count=3, include_original=include)
    queries, trace = rewrite_question("original", config, Settings(_env_file=None))
    assert queries == expected and calls == [{"question": "original", "max_queries": 3}]
    assert trace.details["messages"][1]["content"] == json.dumps(calls[0])
    assert trace.details["usage"] is None and trace.details["state"] == "complete"
    assert trace.details["prompt_version"] == "query-rewrite-v1"


@pytest.mark.parametrize(
    "output",
    [
        "not JSON",
        '{"queries":[]}',
        '{"queries":[""]}',
        '{"queries":[1]}',
        '{"queries":["a","b"]}',
        '{"queries":["a"],"answer":"extra"}',
        '{"queries":["a"],"queries":["b"]}',
        "x" * 16001,
    ],
)
def test_invalid_output_fails_or_explicitly_falls_back(monkeypatch, output):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: output)
    with pytest.raises(RuntimeError, match="no retrieval was scored"):
        rewrite_question(
            "original", RewriteConfig(model="fixture", count=1), Settings(_env_file=None)
        )
    queries, trace = rewrite_question(
        "original",
        RewriteConfig(model="fixture", count=1, failure="original"),
        Settings(_env_file=None),
    )
    assert queries == ["original"] and trace.details["state"] == "fallback_original"
    assert "error_type" in trace.details


def test_provider_failure_preserves_no_secret_in_fallback(monkeypatch):
    def fail(*args):
        raise RuntimeError("provider error with SECRET")

    monkeypatch.setattr(ChatProvider, "answer", fail)
    _, trace = rewrite_question(
        "reset", RewriteConfig(model="fixture", failure="original"), Settings(_env_file=None)
    )
    assert "SECRET" not in trace.model_dump_json()


@pytest.mark.parametrize("helpful", [True, False])
def test_generated_queries_can_help_or_drift_and_never_see_gold(
    tmp_path, m6_corpus, monkeypatch, helpful
):
    path, labels, _ = m6_corpus
    data = json.loads(labels.read_text())
    data["questions"][0]["question"] = "duration reset" if helpful else "reset eight seconds"
    labels.write_text(json.dumps(data))
    seen = []

    def answer(self, system, user):
        seen.append(user)
        return json.dumps(
            {"queries": ["reset eight seconds" if helpful else "power connector USB-C"]}
        )

    monkeypatch.setattr(ChatProvider, "answer", answer)
    config = StrategyConfig(
        name="rewritten",
        strategy="bm25",
        k=1,
        rewrite=RewriteConfig(model="fixture", count=1, include_original=False),
    )
    result = run_portable(path, [], config, output_root=tmp_path / "out", reviewed_file=labels)
    q = result.report["questions"][0]
    assert q["question"] == data["questions"][0]["question"]
    assert q["metrics"]["sufficient_evidence"] is helpful
    assert all(set(json.loads(user)) == {"question", "max_queries"} for user in seen)
    assert "GOLDSECRET" not in " ".join(seen) and "CONDITION" not in " ".join(seen)
    assert q["stages"][0]["name"] == "query_rewriting"
    saved = json.loads((result.directory / "run.json").read_text())
    assert saved["queries"][0]["search_queries"] == [
        "reset eight seconds" if helpful else "power connector USB-C"
    ]
    assert saved["manifest"]["config"]["rewrite"]["endpoint_hash"]


def test_source_only_rewrite_does_not_call_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: pytest.fail("No question to rewrite"))
    path = tmp_path / "manual.txt"
    path.write_text("Reset instructions")
    result = run_portable(
        path,
        [],
        StrategyConfig(name="source", strategy="bm25", rewrite=RewriteConfig(model="fixture")),
        output_root=tmp_path / "out",
    )
    assert result.report["evaluation_level"] == "ingestion_only"


def test_explicit_rewrite_failure_is_visible_in_all_reports(tmp_path, m6_corpus, monkeypatch):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: "invalid")
    result = run_portable(
        m6_corpus[0],
        [SearchQuestion(question_id="Q", question="reset")],
        StrategyConfig(
            name="fallback",
            strategy="bm25",
            rewrite=RewriteConfig(model="fixture", failure="original"),
        ),
        output_root=tmp_path / "out",
        formats=["html", "markdown", "json"],
    )
    for path in result.exports.values():
        assert "fallback" in path.read_text() and "transformation failed" in path.read_text()


def test_failed_rewriting_retains_prompt_and_invalid_output_without_scores(
    tmp_path, m6_corpus, monkeypatch
):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: "invalid model output")
    output = tmp_path / "out"
    with pytest.raises(RuntimeError, match="no retrieval was scored"):
        run_portable(
            m6_corpus[0],
            [SearchQuestion(question_id="Q", question="reset")],
            StrategyConfig(name="failed", strategy="bm25", rewrite=RewriteConfig(model="fixture")),
            output_root=output,
        )
    root = next(output.iterdir())
    failure = json.loads((root / "failure.json").read_text())
    assert failure["question_id"] == "Q"
    assert failure["stage"]["details"]["raw_output"] == "invalid model output"
    assert failure["stage"]["details"]["messages"][1]["content"]
    assert not (root / "evaluation.json").exists() and not (root / "report.html").exists()


def test_oversized_rewrite_prompt_is_bounded_before_the_provider(monkeypatch):
    monkeypatch.setattr(ChatProvider, "answer", lambda *args: pytest.fail("Prompt must be bounded"))
    config = RewriteConfig(model="fixture", failure="original")
    question = "Q" * 100001
    queries, stage = rewrite_question(question, config, Settings(_env_file=None))
    assert queries == [question] and stage.details["state"] == "fallback_original"
    assert "messages" not in stage.details
