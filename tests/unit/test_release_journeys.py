"""Release-level CLI and HTTP contracts; fixtures are synthetic, never real models."""

import json
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ragvidence.cli import app
from ragvidence.config import Settings
from ragvidence.models import CompressionConfig, RewriteConfig, StrategyConfig
from ragvidence.portable import run_portable

FIXTURES = Path(__file__).parents[1] / "fixtures/portable"


@pytest.mark.parametrize("command", ["version", "catalog", "bm25"])
def test_cli_protocols_survive_missing_windows_resource_module(tmp_path, command):
    from ragvidence import __version__

    source = tmp_path / "manual.txt"
    source.write_text("Reset requires eight seconds.", encoding="utf-8")
    arguments = {
        "version": ["--version"],
        "catalog": ["techniques", "--format", "json"],
        "bm25": [
            "bm25",
            str(source),
            "--query",
            "reset",
            "--no-input",
            "--output",
            str(tmp_path / "reports"),
        ],
    }[command]
    code = "import sys; sys.modules['resource'] = None; from ragvidence.cli import app; app()"
    result = subprocess.run(
        [sys.executable, "-c", code, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "resource module not available" not in result.stdout
    if command == "version":
        assert result.stdout.strip() == __version__
    elif command == "catalog":
        assert any(c["name"] == "bm25" for c in json.loads(result.stdout))
    else:
        assert "retrieval_inspection" in result.stdout
        assert "resource module not available" in result.stderr


def test_core_network_is_blocked_by_default():
    with pytest.raises(AssertionError, match="offline"):
        socket.create_connection(("example.com", 443))


def test_core_datagram_network_is_blocked_by_default():
    with (
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as channel,
        pytest.raises(AssertionError, match="offline"),
    ):
        channel.sendto(b"must not leave this process", ("192.0.2.1", 53))


@pytest.mark.parametrize("extension", ["txt", "md"])
def test_empty_text_formats_fail_without_quality_report(tmp_path, extension):
    source = tmp_path / f"empty.{extension}"
    source.write_text(" \n", encoding="utf-8")
    result = CliRunner().invoke(app, ["bm25", str(source), "--query", "reset", "--no-input"])
    assert result.exit_code != 0
    assert "Cannot load" in result.output


@pytest.mark.parametrize(
    "filename",
    [
        "manual.html",
        "documents.json",
        "documents.jsonl",
        "documents.csv",
        "text-pages.pdf",
        "manual.txt",
        "manual.md",
    ],
)
def test_each_loader_has_a_real_cli_to_report_journey(tmp_path, monkeypatch, filename):
    from ragvidence import portable_config

    monkeypatch.setattr(portable_config, "user_config_path", lambda: tmp_path / "no-config.toml")
    source = FIXTURES / filename
    if filename in {"manual.txt", "manual.md"}:
        source = tmp_path / filename
        source.write_text("# Reset\nHold reset for eight seconds.", encoding="utf-8")
    if filename.endswith(".pdf"):
        pytest.importorskip("pypdf")
    result = CliRunner().invoke(
        app,
        [
            "bm25",
            str(source),
            "--query",
            "reset",
            "--format",
            "json",
            "--format",
            "html",
            "--format",
            "markdown",
            "--output",
            str(tmp_path / "out"),
            "--no-input",
        ],
    )
    assert result.exit_code == 0, result.output
    directory = next((tmp_path / "out").iterdir())
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    run = json.loads((directory / "run.json").read_text(encoding="utf-8"))
    assert report["questions"][0]["context_hash"] == run["queries"][0]["context_hash"]
    assert report["evaluation_level"] == "retrieval_inspection"
    assert all(p.is_file() for p in [directory / "report.html", directory / "report.md"])
    assert report["questions"][0]["hits"]


@pytest.mark.loopback
@pytest.mark.parametrize("provider", ["ollama", "openai_compatible"])
def test_local_http_adapters_execute_rewriting_embeddings_and_exact_compression(
    tmp_path,
    m6_corpus,
    provider,
):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append((self.path, data))
            if self.path.endswith(("/api/embed", "/embeddings")):
                vectors = [[1.0, float("eight" in text)] for text in data["input"]]
                value = {
                    "embeddings": vectors,
                    "data": [{"index": i, "embedding": v} for i, v in enumerate(vectors)],
                }
            else:
                prompt = json.loads(data["messages"][1]["content"])
                if "sources" in prompt:
                    source = next(s for s in prompt["sources"] if "eight seconds" in s["body"])
                    output = {
                        "selections": [
                            {
                                "source_unit_id": source["source_unit_id"],
                                "start": 0,
                                "end": len(source["body"]),
                            }
                        ]
                    }
                else:
                    output = {"queries": ["reset eight seconds"]}
                value = {
                    "message": {"content": json.dumps(output)},
                    "choices": [{"message": {"content": json.dumps(output)}}],
                }
            raw = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    endpoint = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        result = run_portable(
            m6_corpus[0],
            [],
            StrategyConfig(
                name="http",
                strategy="semantic",
                k=1,
                provider=provider,
                model="fixture",
                rewrite=RewriteConfig(model="fixture", provider=provider, count=1),
                compression=CompressionConfig(mode="model", model="fixture", provider=provider),
            ),
            output_root=tmp_path / "out",
            reviewed_file=m6_corpus[1],
            cache_dir=tmp_path / "cache",
            settings=Settings(
                _env_file=None, embedding_base_url=endpoint, transform_base_url=endpoint
            ),
        )
        assert all(q["metrics"]["sufficient_evidence"] for q in result.report["questions"])
        assert "GOLDSECRET" not in json.dumps(received)
        assert any(
            path.endswith("/api/chat" if provider == "ollama" else "/chat/completions")
            for path, _ in received
        )
        assert any(
            path.endswith("/api/embed" if provider == "ollama" else "/embeddings")
            for path, _ in received
        )
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
