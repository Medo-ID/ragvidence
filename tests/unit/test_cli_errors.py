from pathlib import Path

from typer.testing import CliRunner

from ragvidence.cli import app

runner = CliRunner()


def test_init_existing_workspace_has_no_traceback(tmp_path: Path) -> None:
    first = runner.invoke(app, ["init", "demo", "--root", str(tmp_path)])
    second = runner.invoke(app, ["init", "demo", "--root", str(tmp_path)])
    assert first.exit_code == 0
    assert second.exit_code == 1
    assert "FAIL" in second.stdout
    assert "Traceback" not in second.stdout


def test_benchmark_missing_dataset_has_actionable_failure(tmp_path: Path) -> None:
    result = runner.invoke(app, ["benchmark", str(tmp_path / "missing")])
    assert result.exit_code == 1
    assert "Cannot read" in result.stdout
    assert "Traceback" not in result.stdout
