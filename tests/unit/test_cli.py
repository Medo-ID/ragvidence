from typer.testing import CliRunner

from raglab.cli import app

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
    assert result.stdout.strip() == "0.1.0"
