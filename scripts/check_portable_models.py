"""Offline integration gate using cached real embeddings, reranker and tokenizer.

Requires ragvidence[semantic]. CACHE/models must be an existing FastEmbed cache.
Does not download models or assert broad benchmark superiority.
"""

import argparse
import hashlib
import json
import os
import tempfile
from importlib.metadata import version
from pathlib import Path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check(cache: Path, output: Path) -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    for key in list(os.environ):
        if key.startswith("RAGVIDENCE_"):
            del os.environ[key]
    from typer.testing import CliRunner

    from ragvidence import portable_config
    from ragvidence.cli import app
    from ragvidence.ingestion import load_corpus

    models = cache / "models"
    if not models.is_dir():
        raise ValueError("Provide a cache root containing an already-populated models directory")
    fingerprints = {
        str(path.relative_to(models)): file_hash(path)
        for path in models.rglob("*")
        if path.is_file() and path.suffix in {".onnx", ".json"}
    }
    tokenizer = next(models.glob("models--Qdrant--*/snapshots/*/tokenizer.json"))
    outcomes = []
    quality_outcomes = []

    def execute(arguments, destination):
        result = CliRunner().invoke(app, arguments)
        if result.exit_code:
            raise RuntimeError(result.output) from result.exception
        return json.loads(next(destination.glob("*/report.json")).read_text())

    with tempfile.TemporaryDirectory(prefix="ragvi-model-gate-") as temporary:
        root = Path(temporary)
        portable_config.user_config_path = lambda: root / "no-user-config.toml"
        source = root / "documents.json"
        source.write_text(
            json.dumps(
                [
                    {"text": "Reset pairing by holding the reset button for eight seconds."},
                    {"text": "Power the device using a USB-C cable."},
                ]
            )
        )
        snapshot = load_corpus(source, exclude=[])
        document = snapshot.documents[0]
        start = document.body.index("eight seconds")
        reviewed = root / "reviewed.json"
        reviewed.write_text(
            json.dumps(
                {
                    "corpus_hash": snapshot.corpus_hash,
                    "evidence": [
                        {
                            "evidence_id": "RESET",
                            "spans": [
                                {
                                    "source_id": document.source_unit_id,
                                    "start": start,
                                    "end": start + 13,
                                    "text": "eight seconds",
                                }
                            ],
                        }
                    ],
                    "questions": [
                        {
                            "question_id": "Q",
                            "question": "How long must I press the pairing button?",
                            "split": "dev",
                            "answerable": True,
                            "required_evidence_ids": ["RESET"],
                        }
                    ],
                }
            )
        )
        for technique in ("semantic", "hybrid", "rerank"):
            destination = root / technique
            arguments = [
                technique,
                str(source),
                "--reviewed",
                str(reviewed),
                "--k",
                "1",
                "--cache-dir",
                str(cache),
                "--output",
                str(destination),
                "--format",
                "json",
                "--no-input",
                "--tokenizer-file",
                str(tokenizer),
                "--context-budget",
                "100",
            ]
            if technique == "rerank":
                arguments += ["--reranker-model", "Xenova/ms-marco-MiniLM-L-6-v2"]
            report = execute(arguments, destination)
            question = report["questions"][0]
            assert question["metrics"]["sufficient_evidence"] is True
            assert question["context_measurement"]["unit"] == "tokens"
            assert 0 < question["context_measurement"]["count"] <= 100
            outcomes.append(
                {
                    "technique": technique,
                    "config": report["manifest"]["config"],
                    "metrics": question["metrics"],
                    "context_measurement": question["context_measurement"],
                    "stage_names": [stage["name"] for stage in question["stages"]],
                }
            )
        fixtures = Path(__file__).resolve().parents[1] / "tests/fixtures/quality"
        corpus = fixtures / "corpus.json"
        specification = json.loads((fixtures / "review.spec.json").read_text())
        frozen = load_corpus(corpus, exclude=[])
        by_key = {source.metadata["record_metadata"]["id"]: source for source in frozen.documents}
        evidence = []
        for item in specification["evidence"]:
            spans = []
            for quote in item["quotes"]:
                source = by_key[quote["id"]]
                assert source.body.count(quote["text"]) == 1
                start = source.body.index(quote["text"])
                spans.append(
                    {
                        "source_id": source.source_unit_id,
                        "start": start,
                        "end": start + len(quote["text"]),
                        "text": quote["text"],
                    }
                )
            evidence.append({"evidence_id": item["evidence_id"], "spans": spans})
        labels = root / "quality-reviewed.json"
        labels.write_text(
            json.dumps(
                {
                    "corpus_hash": frozen.corpus_hash,
                    "evidence": evidence,
                    "questions": specification["questions"],
                }
            )
        )
        configurations = [
            ("lexical", "bm25", []),
            ("bge", "semantic", ["--model", "BAAI/bge-small-en-v1.5"]),
            ("minilm", "semantic", ["--model", "sentence-transformers/all-MiniLM-L6-v2"]),
            ("hybrid", "hybrid", ["--model", "BAAI/bge-small-en-v1.5"]),
            ("reranked", "rerank", ["--reranker-model", "Xenova/ms-marco-MiniLM-L-6-v2"]),
        ]
        for label, technique, extra in configurations:
            destination = root / ("quality-" + label)
            arguments = [
                technique,
                str(corpus),
                "--reviewed",
                str(labels),
                "--k",
                "2",
                "--cache-dir",
                str(cache),
                "--output",
                str(destination),
                "--format",
                "json",
                "--no-input",
                *extra,
            ]
            report = execute(arguments, destination)
            assert report["manifest"]["corpus_hash"] == frozen.corpus_hash
            assert len(report["evaluation"]["questions"]) == 12
            if technique == "semantic":
                paraphrase = next(
                    row
                    for row in report["evaluation"]["questions"]
                    if row["question_id"] == "RESET-PARAPHRASE"
                )
                assert paraphrase["sufficient_evidence"] is True
            assert (
                sum(
                    summary["answerable_questions"]
                    for summary in report["evaluation"]["summaries"].values()
                )
                == 11
            )
            quality_outcomes.append(
                {
                    "configuration": label,
                    "config": report["manifest"]["config"],
                    "corpus_hash": report["manifest"]["corpus_hash"],
                    "references_hash": report["evaluation"]["references_hash"],
                    "summaries": report["evaluation"]["summaries"],
                    "questions": report["evaluation"]["questions"],
                }
            )
            print(f"PASS: reviewed corpus execution for {label}", flush=True)
        assert len({item["references_hash"] for item in quality_outcomes}) == 1
        assert len({item["corpus_hash"] for item in quality_outcomes}) == 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "scope": "offline-real-adapter-compatibility",
                "limitations": "A smoke fixture and a small fictional reviewed corpus; "
                "no general superiority, independent-sample or production-quality claim",
                "packages": {
                    name: version(name) for name in ("fastembed", "onnxruntime", "tokenizers")
                },
                "model_file_sha256": fingerprints,
                "outcomes": outcomes,
                "reviewed_quality_corpus": quality_outcomes,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"PASS: real semantic, hybrid, reranking and tokenizer adapters; evidence in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    options = parser.parse_args()
    check(options.cache_dir, options.output)
