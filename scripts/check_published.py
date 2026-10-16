"""Verify the index wheel matches the built candidate, then exercise installation."""

import argparse
import json
import tempfile
from pathlib import Path

from scripts.check_portable_install import check_install
from scripts.fetch_release import download
from scripts.release_metadata import distributions, release_version, sha256

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", choices=["pypi", "testpypi"], required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--online-install", action="store_true")
    args = parser.parse_args()
    version = release_version()
    wheel = next(p for p in distributions(args.candidate_dir, version) if p.suffix == ".whl")
    with tempfile.TemporaryDirectory(prefix="ragvi-published-") as temporary:
        root = Path(temporary)
        artifact = download(args.index, version, root / "downloads", sha256(wheel))
        installation = root / "installation"
        installation.mkdir()
        result = {
            "index": args.index,
            **check_install(artifact, installation, offline=not args.online_install),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
