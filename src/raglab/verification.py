"""Deterministic installation verification independent of pytest."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from raglab.data import load_dataset
from raglab.evaluation.metrics import sufficient_evidence_at_k
from raglab.representation import build_records
from raglab.strategies.bm25 import BM25Strategy, tokenize
from raglab.workspace import EXERCISE_ROOT, create_workspace, restore_workspace


@dataclass(frozen=True)
class Verification:
    status: str
    name: str
    detail: str


def run_verification() -> list[Verification]:
    checks = [
        _asset_integrity(),
        _dataset_integrity(),
        _tokenizer_fixture(),
        _bm25_fixture(),
        _recovery_fixture(),
        _metrics_fixture(),
    ]
    template = Path(__file__).parent / "reporting/templates/report.html.j2"
    checks.append(
        Verification(
            "PASS" if template.is_file() else "FAIL",
            "HTML template",
            "self-contained template is installed" if template.is_file() else "template is missing",
        )
    )
    return checks


def _asset_integrity() -> Verification:
    expected = json.loads((EXERCISE_ROOT / "integrity.json").read_text(encoding="utf-8"))
    failures = [
        name
        for name, digest in expected.items()
        if hashlib.sha256((EXERCISE_ROOT / name).read_bytes()).hexdigest() != digest
    ]
    return (
        Verification("FAIL", "Asset hashes", f"changed files: {', '.join(failures)}")
        if failures
        else Verification("PASS", "Asset hashes", f"verified {len(expected)} bundled files")
    )


def _dataset_integrity() -> Verification:
    try:
        sources, questions = load_dataset(EXERCISE_ROOT)
    except Exception as exc:
        return Verification("FAIL", "Dataset", str(exc))
    return Verification("PASS", "Dataset", f"{len(sources)} sources; {len(questions)} questions")


def _tokenizer_fixture() -> Verification:
    actual = tokenize("Firmware 4.2 SKU-7722XX")
    expected = ["firmware", "4.2", "sku-7722xx"]
    return Verification(
        "PASS" if actual == expected else "FAIL",
        "Tokenizer",
        "identifier/version fixture preserved" if actual == expected else repr(actual),
    )


def _bm25_fixture() -> Verification:
    sources, _ = load_dataset(EXERCISE_ROOT)
    strategy = BM25Strategy()
    strategy.index(build_records(sources, "heading_context"))
    hits = strategy.search("Orion DeskHub firmware 4.2 pairing reset", k=2)
    found = any(hit.source_unit_id == "SEC-ORION-42-RESET" for hit in hits)
    return Verification(
        "PASS" if found else "FAIL",
        "BM25 fixture",
        "required source found at k=2" if found else "required source missing at k=2",
    )


def _recovery_fixture() -> Verification:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = create_workspace(root, "verify")
        (target / "user-edit.txt").write_text("preserve", encoding="utf-8")
        _, backup = restore_workspace(root, "verify")
        preserved = (backup / "user-edit.txt").read_text(encoding="utf-8") == "preserve"
    return Verification(
        "PASS" if preserved else "FAIL",
        "Recovery",
        "user edit preserved in backup" if preserved else "backup lost user edit",
    )


def _metrics_fixture() -> Verification:
    try:
        result = sufficient_evidence_at_k({"E-1"}, [{"E-1"}], 1)
    except NotImplementedError:
        return Verification("FAIL", "Metrics", "metrics implementation is missing")
    except Exception as exc:
        return Verification("FAIL", "Metrics", str(exc))
    return Verification(
        "PASS" if result is True else "FAIL",
        "Metrics",
        "sufficient-evidence fixture passed" if result is True else repr(result),
    )
