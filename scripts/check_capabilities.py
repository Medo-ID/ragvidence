"""Match capability claims to actual pytest outcomes, never to test names alone."""

import argparse
import json
from pathlib import Path

from ragvidence.capabilities import CAPABILITIES
from scripts.release_metadata import ROOT

REQUIRED_CONTRACTS = {
    *(f"T{number:02d}" for number in range(1, 17)),
    "I01",
    *(f"L{number:02d}" for number in range(1, 8)),
}


def check(evidence: dict, manifest: dict) -> dict:
    if evidence["exit_code"] != 0:
        raise ValueError("The test session did not succeed")
    outcomes = evidence["outcomes"]
    if evidence["collected"] != len(outcomes):
        raise ValueError("Test evidence is incomplete")
    identifiers = [entry["id"] for entry in manifest["capabilities"]]
    if len(set(identifiers)) != len(identifiers) or set(identifiers) != REQUIRED_CONTRACTS:
        raise ValueError(
            "Capability contracts require every planned technique and loader exactly once"
        )
    claimed = {c for entry in manifest["capabilities"] for c in entry["commands"]}
    if claimed != {c.name for c in CAPABILITIES}:
        raise ValueError("Capability contracts do not match the CLI catalog")
    records = []
    for entry in manifest["capabilities"]:
        groups = {}
        for group in ("positive", "negative", "journey"):
            matches = {}
            for selector in entry[group]:
                selected = {
                    node: status
                    for node, status in outcomes.items()
                    if node == selector or node.startswith(selector + "[")
                }
                if not selected or any(status != "passed" for status in selected.values()):
                    raise ValueError(
                        f"{entry['id']} {group}: missing, failed or skipped {selector}"
                    )
                matches.update(selected)
            if not matches:
                raise ValueError(f"{entry['id']} has no {group} contract")
            groups[group] = sorted(matches)
        records.append(
            {
                "id": entry["id"],
                "scope": entry["scope"],
                "status": "passed",
                "contracts": groups,
                "real_model_check": {"status": "separate", "script_output": entry["model_check"]}
                if entry["model_check"]
                else {"status": "not_required"},
            }
        )
    return {
        "schema_version": 1,
        "status": "passed",
        "capabilities": records,
        "limit": "Contract coverage does not guarantee retrieval quality on another corpus.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(
        json.loads(args.tests.read_text(encoding="utf-8")),
        json.loads((ROOT / "scripts/capability_contracts.json").read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
