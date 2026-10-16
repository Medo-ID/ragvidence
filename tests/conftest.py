"""Offline core tests and a machine-readable record of actual test outcomes."""

import json
import socket
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--test-evidence", help="Write per-test outcomes for capability verification")


def pytest_configure(config):
    config.addinivalue_line("markers", "loopback: explicitly allow a local HTTP fixture only")
    config._ragvi_outcomes = {}


@pytest.fixture(autouse=True)
def offline_network(monkeypatch, request):
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    lookup = socket.getaddrinfo
    sendto = socket.socket.sendto
    allowed = request.node.get_closest_marker("loopback") is not None

    def guard(address):
        if not allowed or address[0] not in {"127.0.0.1", "::1", "localhost"}:
            raise AssertionError("Core tests are offline; unexpected network access")

    def safe_connect(sock, address):
        guard(address)
        return connect(sock, address)

    def safe_connect_ex(sock, address):
        guard(address)
        return connect_ex(sock, address)

    def safe_lookup(host, *args, **kwargs):
        guard((host,))
        return lookup(host, *args, **kwargs)

    def safe_sendto(sock, data, *args):
        guard(args[-1])
        return sendto(sock, data, *args)

    monkeypatch.setattr(socket.socket, "connect", safe_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", safe_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", safe_lookup)
    monkeypatch.setattr(socket.socket, "sendto", safe_sendto)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    item.config._ragvi_outcomes.setdefault(item.nodeid, []).append(report.outcome)


def pytest_sessionfinish(session, exitstatus):
    output = session.config.getoption("--test-evidence")
    if output:
        outcomes = session.config._ragvi_outcomes
        status = {
            node: "failed" if "failed" in phases else "skipped" if "skipped" in phases else "passed"
            for node, phases in outcomes.items()
        }
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "exit_code": int(exitstatus),
                    "collected": session.testscollected,
                    "outcomes": status,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
