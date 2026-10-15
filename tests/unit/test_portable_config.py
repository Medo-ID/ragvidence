import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ragvidence import portable_config
from ragvidence.cli import app
from ragvidence.models import InputPreparation
from ragvidence.portable_config import resolve_portable_options


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    for key in os.environ:
        if key.startswith("RAGVIDENCE_"):
            monkeypatch.delenv(key)
    monkeypatch.setattr(portable_config, "user_config_path", lambda: tmp_path / "user.toml")


def test_precedence_for_every_layer_and_paths_relative_to_config(tmp_path, monkeypatch):
    (tmp_path / "user.toml").write_text('k = 3\nchunk_size = 300\noutput = "user-reports"\n')
    explicit = tmp_path / "options.json"
    explicit.write_text(json.dumps({"k": 4, "chunk_size": 400, "cache_dir": "cache"}))
    env = tmp_path / "settings.env"
    env.write_text('RAGVIDENCE_K=5\nRAGVIDENCE_CHUNK_SIZE=450\nRAGVIDENCE_FORMATS=["json"]\n')
    monkeypatch.setenv("RAGVIDENCE_K", "6")
    values = resolve_portable_options({"k": 7}, config_file=explicit, env_file=env)
    assert values.k == 7
    assert values.chunk_size == 450
    assert values.formats == ["json"]
    assert values.output == tmp_path / "user-reports"
    assert values.cache_dir == tmp_path / "cache"
    assert resolve_portable_options({}, config_file=explicit, env_file=env).k == 6
    monkeypatch.delenv("RAGVIDENCE_K")
    assert resolve_portable_options({}, config_file=explicit, env_file=env).k == 5
    assert resolve_portable_options({}, config_file=explicit).k == 4
    assert resolve_portable_options({}).k == 3
    (tmp_path / "user.toml").unlink()
    assert resolve_portable_options({}).k == 2


def test_cwd_config_and_dotenv_are_never_discovered(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("RAGVIDENCE_K=99")
    Path("config.toml").write_text("k = 88")
    assert resolve_portable_options({}).k == 2


@pytest.mark.parametrize(
    "raw,reason",
    [
        ("unknown = 1", "Unknown portable"),
        ("k = 0", "greater than or equal"),
        ("chunk_size = 50\nchunk_overlap = 50", "chunk-overlap"),
        ('formats = ["pdf"]', "Supported report formats"),
        ("output = 5", "path string"),
        ("formats = []", "Supported report formats"),
        ("invalid toml", "Expected"),
    ],
)
def test_invalid_config_fails_before_creating_outputs(tmp_path, raw, reason):
    config = tmp_path / "options.toml"
    config.write_text(raw)
    source = tmp_path / "manual.txt"
    source.write_text("Reset the device")
    output = tmp_path / "out"
    result = CliRunner().invoke(
        app, ["bm25", str(source), "--config", str(config), "--output", str(output), "--no-input"]
    )
    assert result.exit_code != 0
    assert reason in result.output
    assert not output.exists()
    assert "Traceback" not in result.output


def test_environment_list_values_require_json_arrays(monkeypatch):
    monkeypatch.setenv("RAGVIDENCE_INCLUDE_PATTERNS", '["*.md", "*.json"]')
    assert resolve_portable_options({}).include_patterns == ["*.md", "*.json"]
    monkeypatch.setenv("RAGVIDENCE_INCLUDE_PATTERNS", "*.md")
    with pytest.raises(ValueError, match="JSON array"):
        resolve_portable_options({})


def test_platform_config_paths(monkeypatch, tmp_path):
    monkeypatch.undo()
    monkeypatch.setattr(portable_config.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    assert portable_config.user_config_path() == tmp_path / "roaming/ragvidence/config.toml"
    monkeypatch.setattr(portable_config.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert portable_config.user_config_path() == tmp_path / "config/ragvidence/config.toml"
    monkeypatch.setattr(portable_config.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert (
        portable_config.user_config_path()
        == tmp_path / "Library/Application Support/ragvidence/config.toml"
    )


def test_explicit_config_env_and_questions_are_excluded_from_folder_and_secrets_from_report(
    tmp_path,
):
    source = tmp_path / "data"
    source.mkdir()
    (source / "records.json").write_text('[{"custom":"Hold reset eight seconds"}]')
    question_file = source / "questions.json"
    question_file.write_text('["reset"]')
    config = source / "options.json"
    config.write_text(
        json.dumps(
            {
                "text_field": "custom",
                "formats": ["json", "html", "markdown"],
                "chunk_size": 100,
                "chunk_overlap": 10,
            }
        )
    )
    env = source / "settings.env"
    env.write_text("RAGVIDENCE_EMBEDDING_API_KEY=MY_PRIVATE_CREDENTIAL\nRAGVIDENCE_K=1\n")
    output = tmp_path / "out"
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(source),
            "--config",
            str(config),
            "--env-file",
            str(env),
            "--questions",
            str(question_file),
            "--output",
            str(output),
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    root = next(output.iterdir())
    report = json.loads((root / "report.json").read_text())
    assert report["input"]["file_count"] == 1
    assert report["manifest"]["config"]["k"] == 1
    assert report["questions"][0]["hits"][0]["location"]["text_field"] == "custom"
    assert "Field custom" in (root / "report.html").read_text()
    assert "Field custom" in (root / "report.md").read_text()
    assert "MY_PRIVATE_CREDENTIAL" not in result.output
    for artifact in root.iterdir():
        assert "MY_PRIVATE_CREDENTIAL" not in artifact.read_text()


def test_cli_flags_override_environment_and_config_formats(tmp_path, monkeypatch):
    source = tmp_path / "manual.txt"
    source.write_text("Reset the device")
    monkeypatch.setenv("RAGVIDENCE_K", "5")
    monkeypatch.setenv("RAGVIDENCE_FORMATS", '["html"]')
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(source),
            "--query",
            "reset",
            "--k",
            "1",
            "--format",
            "json",
            "--output",
            str(tmp_path / "out"),
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    root = next((tmp_path / "out").iterdir())
    report = json.loads((root / "report.json").read_text())
    assert report["manifest"]["config"]["k"] == 1
    assert not (root / "report.html").exists()


def test_legacy_preparation_serializes_without_changing_original_identity():
    legacy = {
        "implementation": "portable-text-v1",
        "length_unit": "characters",
        "chunk_size": 500,
        "chunk_overlap": 50,
    }
    assert InputPreparation.model_validate(legacy).model_dump(mode="json") == legacy
