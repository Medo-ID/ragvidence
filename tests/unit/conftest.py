"""Small independently reviewed fixtures shared by stage-contract tests."""

import json

import numpy as np
import pytest

from ragvidence import pipeline
from ragvidence.ingestion import load_corpus
from ragvidence.strategies.semantic import SemanticStrategy


@pytest.fixture
def m6_corpus(tmp_path):
    path = tmp_path / "manuals.json"
    path.write_text(
        json.dumps(
            [
                {
                    "text": "Reset reset reset by holding for one second.",
                    "version": 1,
                    "product": "A",
                },
                {
                    "text": "Reset by holding for eight seconds. "
                    "Only with power disconnected. Warranty is two years.",
                    "version": 2,
                    "product": "A",
                },
                {"text": "Use the USB-C power connector.", "version": 2, "product": "B"},
            ]
        )
    )
    snapshot = load_corpus(path, exclude=[])
    original = snapshot.documents[1]
    evidence = []
    for evidence_id, quote in (
        ("DURATION", "eight seconds"),
        ("CONDITION", "Only with power disconnected"),
    ):
        start = original.body.index(quote)
        evidence.append(
            {
                "evidence_id": evidence_id,
                "spans": [
                    {
                        "source_id": original.source_unit_id,
                        "start": start,
                        "end": start + len(quote),
                        "text": quote,
                    }
                ],
            }
        )
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps(
            {
                "corpus_hash": snapshot.corpus_hash,
                "evidence": evidence,
                "questions": [
                    {
                        "question_id": question_id,
                        "question": "reset",
                        "split": split,
                        "answerable": True,
                        "required_evidence_ids": ["DURATION", "CONDITION"],
                        "reference_answer": "GOLDSECRET",
                    }
                    for question_id, split in (("Q", "dev"), ("H", "heldout"))
                ],
            }
        )
    )
    return path, labels, snapshot


@pytest.fixture
def m6_embeddings(monkeypatch, tmp_path):
    observed = []

    class Embeddings:
        model_name = "stage-fixture"
        cache_identity = {"adapter": "fixture", "model": "stage-fixture", "revision": "1"}

        def embed_documents(self, texts):
            observed.extend(texts)
            return np.array([[1.0, float("eight" in t), float("power" in t)] for t in texts])

        def embed_query(self, text):
            observed.append(text)
            return np.array([1.0, float("eight" in text), float("power" in text)])

    monkeypatch.setattr(
        pipeline,
        "semantic_strategy",
        lambda config, cache_dir, settings: SemanticStrategy(
            provider=Embeddings(),
            cache_dir=tmp_path / "fixture-embeddings",
        ),
    )
    return observed
