"""Ordinary-file workflows must work without a manually prepared workspace."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ragvidence.cli import app


def exported(output: Path, name: str):
    paths = list(output.glob(f"*/{name}"))
    assert len(paths) == 1
    return paths[0]


def test_raw_text_query_creates_reports_and_exact_passages(tmp_path):
    source = tmp_path / "Device α manual.txt"
    original = "Pairing reset: hold the button for eight seconds.\n\nPower: use USB-C.\n"
    source.write_text(original, encoding="utf-8")
    output = tmp_path / "exports"
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(source),
            "--query",
            "pairing reset",
            "--output",
            str(output),
            "--format",
            "html",
            "--format",
            "json",
            "--format",
            "markdown",
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "retrieval_inspection" in result.output
    assert "eight seconds" in result.output
    report = json.loads(exported(output, "report.json").read_text())
    assert report["evaluation_level"] == "retrieval_inspection"
    assert report["questions"][0]["question"] == "pairing reset"
    assert "sufficient_evidence" not in report["questions"][0]
    assert "eight seconds" in exported(output, "report.html").read_text()
    assert "pairing reset" in exported(output, "report.md").read_text()
    run = json.loads(exported(output, "run.json").read_text())
    assert run["manifest"]["hash_algorithm"] == "canonical-json-v1"
    assert run["manifest"]["input_preparation"] == report["preparation"]
    assert run["queries"][0]["rendered_context"]
    assert source.read_text() == original
    assert not (tmp_path / "workspaces").exists()


def test_source_only_report_does_not_run_retrieval(tmp_path, monkeypatch):
    from ragvidence import runner

    def unexpected(*args, **kwargs):
        pytest.fail("Source diagnostics must not initialize a retrieval model")

    monkeypatch.setattr(runner, "build_strategy", unexpected)
    source = tmp_path / "manual.md"
    source.write_text("# Device\n\nReset pairing with the button.")
    output = tmp_path / "reports"
    result = CliRunner().invoke(app, ["bm25", str(source), "--no-input", "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert "ingestion_only" in result.output
    assert "not executed" in exported(output, "report.html").read_text()


def test_question_file_inside_input_folder_is_excluded(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "manual.txt").write_text("Hold the button for eight seconds to reset.")
    question_file = folder / "questions.txt"
    question_file.write_text("How long do I hold the button?\nHow do I reset?\n")
    output = folder / "custom-results"
    output.mkdir()
    (output / "must-not-ingest.txt").write_text("SECRET DISTRACTOR")
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(folder),
            "--questions",
            str(question_file),
            "--output",
            str(output),
            "--format",
            "json",
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    report = json.loads(exported(output, "report.json").read_text())
    assert report["input"]["document_count"] == 1
    assert len(report["questions"]) == 2
    assert "SECRET DISTRACTOR" not in exported(output, "snapshot.json").read_text()


def test_repeated_runs_use_unique_directories_and_stable_snapshot(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("A device reset needs eight seconds.")
    output = tmp_path / "reports"
    args = ["bm25", str(source), "--query", "reset", "--output", str(output), "--no-input"]
    runner = CliRunner()
    assert runner.invoke(app, args).exit_code == 0
    assert runner.invoke(app, args).exit_code == 0
    snapshots = list(output.glob("*/snapshot.json"))
    assert len(snapshots) == 2
    assert snapshots[0].read_bytes() == snapshots[1].read_bytes()


@pytest.mark.parametrize(
    "arguments",
    [["--format", "pdf"], ["--k", "0"], ["--query", " "], ["--interactive", "--no-input"]],
)
def test_invalid_requests_fail_before_output_creation(tmp_path, arguments):
    source = tmp_path / "manual.txt"
    source.write_text("Text")
    output = tmp_path / "reports"
    result = CliRunner().invoke(app, ["bm25", str(source), "--output", str(output), *arguments])
    assert result.exit_code != 0
    assert not output.exists()
    assert "Traceback" not in result.output


def test_prompt_collects_question_without_project_setup(tmp_path, monkeypatch):
    from ragvidence import portable_cli

    monkeypatch.setattr(portable_cli, "input_is_terminal", lambda: True)
    source = tmp_path / "manual.txt"
    source.write_text("Hold reset for eight seconds.")
    result = CliRunner().invoke(
        app, ["bm25", str(source), "--output", str(tmp_path / "out")], input="How long for reset?\n"
    )
    assert result.exit_code == 0, result.output
    assert "retrieval_inspection" in result.output


def test_document_html_is_escaped_in_report(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text('<script>alert("x")</script> reset instructions')
    output = tmp_path / "out"
    result = CliRunner().invoke(
        app, ["bm25", str(source), "--query", "reset", "--output", str(output), "--no-input"]
    )
    assert result.exit_code == 0, result.output
    report = exported(output, "report.html").read_text()
    assert "<script>alert" not in report
    assert "&lt;script&gt;" in report


def test_portable_bm25_does_not_read_cwd_env_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("RAGVIDENCE_EMBEDDING_PROVIDER=invalid\nRAGVIDENCE_GENERATION_MODEL=x")
    Path("manual.txt").write_text("Reset for eight seconds.")
    result = CliRunner().invoke(app, ["bm25", "manual.txt", "--query", "reset", "--no-input"])
    assert result.exit_code == 0, result.output
    assert list(Path("ragvi-reports").glob("*/report.html"))


def test_failed_execution_keeps_an_explicit_failure_artifact(tmp_path):
    source = tmp_path / "punctuation.txt"
    source.write_text("... !!! ---")
    output = tmp_path / "reports"
    result = CliRunner().invoke(
        app, ["bm25", str(source), "--query", "reset", "--output", str(output), "--no-input"]
    )
    assert result.exit_code == 1
    assert "no searchable words" in result.output
    assert json.loads(exported(output, "status.json").read_text())["state"] == "failed"
    assert not list(output.glob("*/report.html"))
    assert "Traceback" not in result.output


def test_report_does_not_open_a_browser_without_the_flag(tmp_path, monkeypatch):
    from ragvidence import portable_cli

    monkeypatch.setattr(
        portable_cli.webbrowser,
        "open",
        lambda *args: pytest.fail("A report must not open a browser without --open"),
    )
    source = tmp_path / "manual.txt"
    source.write_text("Reset instructions")
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(source),
            "--query",
            "reset",
            "--no-input",
            "--output",
            str(tmp_path / "reports"),
        ],
    )
    assert result.exit_code == 0, result.output
