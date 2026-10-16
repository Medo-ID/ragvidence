"""Download only the requested project's wheel from an official package index."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen


def download(index: str, version: str, directory: Path, expected_sha256: str | None = None) -> Path:
    if index not in {"pypi", "testpypi"}:
        raise ValueError("Use pypi or testpypi")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", version):
        raise ValueError("Use an exact release version")
    origin = "pypi.org" if index == "pypi" else "test.pypi.org"
    metadata_url = f"https://{origin}/pypi/ragvidence/{version}/json"
    with urlopen(metadata_url, timeout=30) as response:  # nosec B310: fixed HTTPS origin
        raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Package metadata exceeds the safety limit")
    value = json.loads(raw)
    filename = f"ragvidence-{version}-py3-none-any.whl"
    matches = [item for item in value["urls"] if item["filename"] == filename]
    if (
        value["info"]["name"] != "ragvidence"
        or value["info"]["version"] != version
        or len(matches) != 1
    ):
        raise ValueError("Index did not return the exact requested release wheel")
    record = matches[0]
    digest = record["digests"]["sha256"]
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("Published wheel differs from the verified candidate checksum")
    url = urlsplit(record["url"])
    if url.scheme != "https" or url.hostname not in {
        "files.pythonhosted.org",
        "test-files.pythonhosted.org",
    }:
        raise ValueError("Wheel URL must use an official HTTPS file host")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError("Cached wheel does not match official metadata")
        return target
    with urlopen(record["url"], timeout=60) as response:  # nosec B310: official host validated above
        content = response.read(50 * 1024 * 1024 + 1)
    if len(content) > 50 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("Wheel download exceeds the limit or fails checksum verification")
    with target.open("xb") as stream:
        stream.write(content)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", choices=["pypi", "testpypi"], required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    print(download(args.index, args.version, args.output, args.expected_sha256).resolve())
