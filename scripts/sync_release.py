"""Bootstrap locked CI dependencies and retain diagnostics even if setup fails."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def sync(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    command = ["uv", "sync", "--frozen", "--dev", "--all-extras"]
    start = time.monotonic()
    with (output / "setup.log").open("wb") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    (output / "setup.json").write_text(
        json.dumps(
            {
                "command": command,
                "status": "passed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "seconds": time.monotonic() - start,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print((output / "setup.log").read_text(encoding="utf-8", errors="replace"))
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("verification/ci"))
    args = parser.parse_args()
    sys.exit(sync(args.output))
