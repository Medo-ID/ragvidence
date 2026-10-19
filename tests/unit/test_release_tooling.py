"""Guard release identity, honest evidence gates and exact-index downloads."""

import hashlib
import io
import json

import pytest

from scripts import fetch_release
from scripts.check_capabilities import check
from scripts.check_distributions import check_members
from scripts.release_metadata import ROOT, distributions, release_version


def test_release_identity_matches_runtime_package_and_lock():
    from ragvidence import __version__

    assert release_version() == __version__


@pytest.mark.parametrize(
    "name",
    [
        "../secret",
        "/root/key",
        "x/.env",
        "x/.git/config",
        "x/maintainer/notes.md",
        "x/instructions.md",
        "x/cache.pyc",
    ],
)
def test_distribution_rejects_private_or_unsafe_members(name):
    with pytest.raises(ValueError):
        check_members([name])


def test_stale_distribution_cannot_enter_a_release(tmp_path):
    for name in [
        "ragvidence-0.2.0-py3-none-any.whl",
        "ragvidence-0.2.0.tar.gz",
        "ragvidence-0.1.0.tar.gz",
    ]:
        (tmp_path / name).touch()
    with pytest.raises(ValueError, match="exactly"):
        distributions(tmp_path, "0.2.0")


@pytest.mark.parametrize("status", ["skipped", "failed", "absent"])
def test_capability_contract_cannot_pass_from_skipped_failed_or_absent_tests(status):
    manifest = json.loads((ROOT / "scripts/capability_contracts.json").read_text(encoding="utf-8"))
    outcomes = {
        selector: "passed"
        for entry in manifest["capabilities"]
        for group in ("positive", "negative", "journey")
        for selector in entry[group]
    }
    target = manifest["capabilities"][0]["positive"][0]
    if status == "absent":
        outcomes.pop(target)
    else:
        outcomes[target] = status
    with pytest.raises(ValueError, match="missing, failed or skipped"):
        check({"exit_code": 0, "collected": len(outcomes), "outcomes": outcomes}, manifest)


@pytest.mark.parametrize("change", ["missing_modifier", "duplicate_loader"])
def test_contract_manifest_cannot_omit_a_modifier_or_duplicate_a_loader(change):
    manifest = json.loads((ROOT / "scripts/capability_contracts.json").read_text(encoding="utf-8"))
    if change == "missing_modifier":
        manifest["capabilities"] = [c for c in manifest["capabilities"] if c["id"] != "T05"]
    else:
        manifest["capabilities"].append(manifest["capabilities"][-1])
    with pytest.raises(ValueError, match="exactly once"):
        check({"exit_code": 0, "collected": 0, "outcomes": {}}, manifest)


@pytest.mark.parametrize("change", ["checksum", "host", "version", "candidate"])
def test_download_rejects_wrong_release_origin_or_bytes(tmp_path, monkeypatch, change):
    content = b"fixture wheel"
    checksum = hashlib.sha256(content).hexdigest()
    metadata = {
        "info": {"name": "ragvidence", "version": "0.2.0"},
        "urls": [
            {
                "filename": "ragvidence-0.2.0-py3-none-any.whl",
                "url": "https://files.pythonhosted.org/packages/wheel.whl",
                "digests": {"sha256": checksum},
            }
        ],
    }
    if change == "host":
        metadata["urls"][0]["url"] = "https://untrusted.example/wheel.whl"
    if change == "version":
        metadata["info"]["version"] = "0.1.0"
    if change == "checksum":
        content = b"wrong wheel bytes"
    responses = iter([json.dumps(metadata).encode(), content])
    monkeypatch.setattr(fetch_release, "urlopen", lambda *a, **k: io.BytesIO(next(responses)))
    expected = "0" * 64 if change == "candidate" else checksum
    with pytest.raises(ValueError):
        fetch_release.download("testpypi", "0.2.0", tmp_path, expected)
    assert not list(tmp_path.iterdir())


def test_download_installs_no_dependencies_and_verifies_exact_wheel(tmp_path, monkeypatch):
    content = b"fixture"
    checksum = hashlib.sha256(content).hexdigest()
    metadata = {
        "info": {"name": "ragvidence", "version": "0.2.0"},
        "urls": [
            {
                "filename": "ragvidence-0.2.0-py3-none-any.whl",
                "url": "https://test-files.pythonhosted.org/packages/exact.whl",
                "digests": {"sha256": checksum},
            }
        ],
    }
    seen = []

    def response(url, **kwargs):
        seen.append(url)
        return io.BytesIO(json.dumps(metadata).encode() if url.endswith("/json") else content)

    monkeypatch.setattr(fetch_release, "urlopen", response)
    artifact = fetch_release.download("testpypi", "0.2.0", tmp_path, checksum)
    assert artifact.read_bytes() == content
    assert len(seen) == 2
    assert seen[0] == "https://test.pypi.org/pypi/ragvidence/0.2.0/json"


def test_failed_gate_surfaces_retained_log_in_public_ci_annotation(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    from scripts import verify_release

    def failed_command(argv, **kwargs):
        kwargs["stdout"].write("Synthetic failure: 50%\nsecond line\n")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(verify_release, "git_identity", lambda: {"commit": "synthetic"})
    monkeypatch.setattr(verify_release.subprocess, "run", failed_command)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(RuntimeError, match="lint failed"):
        verify_release.verify(tmp_path, tmp_path / "dist")
    output = capsys.readouterr()
    assert "Synthetic failure: 50%\nsecond line" in output.err
    assert "::error title=lint failed::Synthetic failure: 50%25%0Asecond line" in output.out
    assert json.loads((tmp_path / "checks.json").read_text())["status"] == "failed"
    assert (tmp_path / "lint.log").read_text() == "Synthetic failure: 50%\nsecond line\n"
