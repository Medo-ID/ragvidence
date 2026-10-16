from pathlib import Path

from typer.testing import CliRunner

from ragvidence import __version__
from ragvidence.cli import app

runner = CliRunner()


def test_health_command_reports_environment_status() -> None:
    result = runner.invoke(app, ["health"])

    assert result.exit_code == 0
    assert "PASS" in result.stdout
    assert "Bundled exercise" in result.stdout
    assert "Privacy" in result.stdout


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_edition_command_identifies_free_build() -> None:
    result = runner.invoke(app, ["edition"])

    assert result.exit_code == 0
    assert "Free" in result.stdout
    assert "no account or activation required" in result.stdout


def test_tutorial_runs_complete_local_workflow(tmp_path: Path) -> None:
    result = runner.invoke(app, ["tutorial", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "COMPLETE" in result.stdout
    assert (tmp_path / "first-run/reports/tutorial.html").is_file()
    assert (tmp_path / "first-run/evaluations/bm25-body.json").is_file()
    assert (tmp_path / "first-run/evaluations/bm25-heading_context.json").is_file()


def test_tutorial_existing_workspace_is_actionable(tmp_path: Path) -> None:
    assert runner.invoke(app, ["tutorial", "--root", str(tmp_path)]).exit_code == 0
    result = runner.invoke(app, ["tutorial", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "workspace already exists" in result.stdout
    assert "--name" in result.stdout
    assert "Traceback" not in result.stdout
