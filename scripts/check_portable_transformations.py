"""Bounded M6 compatibility check against an already-installed local Ollama model.

No downloads, answer generation, judge or optimization. Model digest is checked
before/after at most two calls. Retains actual valid/invalid outputs and quality
outcomes without requiring every transformation to improve retrieval.
"""

import argparse
import json
import tempfile
from pathlib import Path
from urllib.request import urlopen

from ragvidence.config import Settings
from ragvidence.ingestion import load_corpus
from ragvidence.models import CompressionConfig, RewriteConfig, StrategyConfig
from ragvidence.portable import run_portable
from ragvidence.providers.remote import _validate_http_url


def model_identity(endpoint: str, model: str) -> dict:
    url = endpoint.rstrip("/") + "/api/tags"
    _validate_http_url(url)
    with urlopen(url, timeout=10) as response:  # nosec B310: URL validated above
        models = json.loads(response.read(1024 * 1024))["models"]
    matches = [item for item in models if item["name"] == model]
    if len(matches) != 1:
        raise ValueError("The requested model must already be installed in Ollama")
    return {
        "model": model,
        "digest": matches[0]["digest"],
        "details": matches[0].get("details", {}),
    }


def check(endpoint: str, model: str, output: Path, expected_digest: str | None):
    before = model_identity(endpoint, model)
    if expected_digest is not None and before["digest"] != expected_digest:
        raise ValueError("Installed transformation model digest differs from the pinned identity")
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="ragvi-m6-transform-") as temporary:
        root = Path(temporary)
        source = root / "manual.txt"
        source.write_text(
            "Reset pairing by holding the button for eight seconds. "
            "Disconnect power before resetting. The warranty is two years."
        )
        snapshot = load_corpus(source, exclude=[])
        document = snapshot.documents[0]
        labels = root / "reviewed.json"
        evidence = []
        for name, quote in (
            ("DURATION", "eight seconds"),
            ("CONDITION", "Disconnect power before resetting"),
        ):
            start = document.body.index(quote)
            evidence.append(
                {
                    "evidence_id": name,
                    "spans": [
                        {
                            "source_id": document.source_unit_id,
                            "start": start,
                            "end": start + len(quote),
                            "text": quote,
                        }
                    ],
                }
            )
        labels.write_text(
            json.dumps(
                {
                    "corpus_hash": snapshot.corpus_hash,
                    "evidence": evidence,
                    "questions": [
                        {
                            "question_id": "Q",
                            "question": "How long must I hold the pairing button, "
                            "and what must I disconnect?",
                            "split": "dev",
                            "answerable": True,
                            "required_evidence_ids": ["DURATION", "CONDITION"],
                        }
                    ],
                }
            )
        )
        for name, modifiers in (
            (
                "rewrite",
                {
                    "rewrite": RewriteConfig(
                        model=model, count=2, max_output_tokens=512, timeout_seconds=120
                    )
                },
            ),
            (
                "compression",
                {
                    "compression": CompressionConfig(
                        mode="model", model=model, max_output_tokens=1024, timeout_seconds=120
                    )
                },
            ),
        ):
            destination = root / name
            try:
                result = run_portable(
                    source,
                    [],
                    StrategyConfig(name=name, strategy="bm25", k=1, **modifiers),
                    output_root=destination,
                    formats=["json"],
                    reviewed_file=labels,
                    settings=Settings(_env_file=None, transform_base_url=endpoint),
                )
                q = result.report["questions"][0]
                outcomes.append(
                    {
                        "technique": name,
                        "status": "passed",
                        "config": result.report["manifest"]["config"],
                        "metrics": q["metrics"],
                        "stages": q["stages"],
                        "context": q["hits"],
                        "query_ms": q["query_time_ms"],
                    }
                )
            except RuntimeError:
                failure_paths = list(destination.glob("*/failure.json"))
                outcomes.append(
                    {
                        "technique": name,
                        "status": "failed",
                        "failure": json.loads(failure_paths[0].read_text())
                        if failure_paths
                        else None,
                    }
                )
    after = model_identity(endpoint, model)
    if before != after:
        raise ValueError("Transformation model identity changed during compatibility check")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "scope": "local-ollama-M6-compatibility",
                "model_identity": before,
                "limitations": "One fictional reviewed question; records compatibility and "
                "exact outputs, not general quality. Provider token usage/truncation are unknown.",
                "outcomes": outcomes,
            },
            indent=2,
        )
        + "\n"
    )
    for outcome in outcomes:
        print(f"{outcome['status'].upper()}: {outcome['technique']}", flush=True)
    if any(outcome["status"] != "passed" for outcome in outcomes):
        raise RuntimeError(f"A transformation failed; inspect {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://localhost:11434")
    parser.add_argument("--model", required=True)
    parser.add_argument("--expected-digest")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    check(args.endpoint, args.model, args.output, args.expected_digest)
