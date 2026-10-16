"""Validate release contents, metadata, license and checksums without installing."""

import argparse
import email
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from scripts.release_metadata import ROOT, distributions, git_identity, release_version, sha256

FORBIDDEN = {
    ".git",
    ".env",
    ".venv",
    "__pycache__",
    ".ragvidence-cache",
    "workspaces",
    "ragvi-reports",
    "maintainer",
}


def check_members(names: list[str]):
    for name in names:
        parts = PurePosixPath(name).parts
        if (
            ".." in parts
            or name.startswith("/")
            or FORBIDDEN.intersection(parts)
            or name.endswith((".pyc", ".log"))
        ):
            raise ValueError(f"Forbidden distribution member: {name}")
        if name.endswith("/instructions.md"):
            raise ValueError(f"Maintainer handoff must not be distributed: {name}")


def inspect_wheel(path: Path, version: str) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        check_members(names)
        required = [
            "ragvidence/capabilities.py",
            "ragvidence/portable.py",
            "ragvidence/compression.py",
            "ragvidence/suites/execution.py",
            "ragvidence/reporting/templates/inspection.html.j2",
            "ragvidence/reporting/templates/comparison.html.j2",
            "ragvidence/reporting/fonts/LICENSE.txt",
            "ragvidence/exercises/heading_context/integrity.json",
        ]
        if not set(required) <= set(names):
            raise ValueError("Wheel is missing required CLI assets")
        metadata = email.message_from_bytes(
            archive.read(next(n for n in names if n.endswith(".dist-info/METADATA")))
        )
        if metadata["Name"] != "ragvidence" or metadata["Version"] != version:
            raise ValueError("Wheel identity differs from release")
        if metadata["License-Expression"] != "Apache-2.0":
            raise ValueError("Wheel must carry Apache-2.0 metadata")
        if set(metadata.get_all("Provides-Extra", [])) != {"pdf", "semantic"}:
            raise ValueError("Wheel optional capabilities are inconsistent")
        if (
            metadata["Requires-Python"] != ">=3.12,<3.13"
            and metadata["Requires-Python"] != "<3.13,>=3.12"
        ):
            raise ValueError("Wheel Python support differs from the tested contract")
        for license_name in [
            "LICENSE.md",
            "NOTICE",
            "THIRD_PARTY_NOTICES.md",
            "THIRD_PARTY_LICENSES.md",
        ]:
            target = next(
                (n for n in names if n.endswith(".dist-info/licenses/" + license_name)), None
            )
            if target is None or archive.read(target) != (ROOT / license_name).read_bytes():
                raise ValueError(f"Wheel license/notice differs: {license_name}")
    return {"status": "passed", "member_count": len(names)}


def inspect_sdist(path: Path, version: str) -> dict:
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        check_members(names)
        if any(m.issym() or m.islnk() or m.isdev() for m in members):
            raise ValueError("Source distribution must contain only regular files/directories")
        prefix = f"ragvidence-{version}/"
        required = {
            prefix + n
            for n in [
                "LICENSE.md",
                "NOTICE",
                "CONTRIBUTING.md",
                "pyproject.toml",
                "uv.lock",
                "docs/portable-advanced-techniques.md",
                "docs/examples/portable-m6-suite.json",
                "src/ragvidence/portable.py",
                "tests/conftest.py",
                "scripts/check_distributions.py",
            ]
        }
        if not required <= set(names):
            raise ValueError("Source distribution is missing release documentation or checks")
    return {"status": "passed", "member_count": len(names)}


def check(directory: Path, tag: str | None = None) -> dict:
    version = release_version()
    if tag is not None and tag != f"v{version}":
        raise ValueError("Git tag does not match the release version")
    files = distributions(directory, version)
    record = {"schema_version": 1, "version": version, "source": git_identity(), "artifacts": {}}
    for path in files:
        result = (
            inspect_wheel(path, version) if path.suffix == ".whl" else inspect_sdist(path, version)
        )
        record["artifacts"][path.name] = {
            **result,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
    (directory / "SHA256SUMS.txt").write_text(
        "".join(f"{record['artifacts'][p.name]['sha256']}  {p.name}\n" for p in files),
        encoding="utf-8",
    )
    (directory / "provenance.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist/release")
    parser.add_argument("--tag")
    args = parser.parse_args()
    print(json.dumps(check(args.dist, args.tag), indent=2))
