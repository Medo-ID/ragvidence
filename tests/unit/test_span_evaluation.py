import json

import pytest

from ragvidence.artifacts import content_hash
from ragvidence.evaluation.spans import completed_evidence, merged_intervals, score_spans
from ragvidence.ingestion import load_corpus
from ragvidence.models import (
    ContextPassage,
    ExperimentRun,
    QueryRun,
    RetrievalHit,
    SearchQuestion,
    StrategyConfig,
)
from ragvidence.portable import run_portable
from ragvidence.portable_validation import validate_portable_run
from ragvidence.reviewed import EvidenceItem, ReviewedReferences
from ragvidence.runner import build_manifest


def passage(start, end, source="D", text="0123456789"):
    return ContextPassage(
        source_unit_id=f"{source}-{start}-{end}",
        origin_source_id=source,
        document_id=source,
        start=start,
        end=end,
        text=text[start:end],
    )


def test_evidence_requires_complete_union_and_never_counts_overlap_twice():
    items = [
        EvidenceItem(
            evidence_id="E", spans=[{"source_id": "D", "start": 2, "end": 8, "text": "234567"}]
        )
    ]
    assert not completed_evidence(items, [passage(2, 5), passage(2, 5)])
    assert not completed_evidence(items, [passage(2, 5), passage(6, 8)])
    assert completed_evidence(items, [passage(2, 5), passage(5, 8)]) == {"E"}
    assert completed_evidence(items, [passage(0, 6), passage(4, 10), passage(4, 10)]) == {"E"}
    assert merged_intervals([(4, 10), (0, 6), (12, 15)]) == [(0, 10), (12, 15)]


def test_multispan_multisource_fact_and_prefix_text_cannot_earn_credit():
    items = [
        EvidenceItem(
            evidence_id="E",
            spans=[
                {"source_id": "D", "start": 0, "end": 2, "text": "01"},
                {"source_id": "OTHER", "start": 8, "end": 10, "text": "89"},
            ],
        )
    ]
    assert not completed_evidence(items, [passage(0, 10)])
    assert completed_evidence(items, [passage(0, 2), passage(8, 10, "OTHER")]) == {"E"}


def reviewed_file(tmp_path, snapshot, quote="eight seconds", split="dev"):
    document = snapshot.documents[0]
    start = document.body.index(quote)
    value = {
        "schema_version": 1,
        "corpus_hash": snapshot.corpus_hash,
        "evidence": [
            {
                "evidence_id": "RESET",
                "spans": [
                    {
                        "source_id": document.source_unit_id,
                        "start": start,
                        "end": start + len(quote),
                        "text": quote,
                    }
                ],
            }
        ],
        "questions": [
            {
                "question_id": "Q",
                "question": "reset",
                "split": split,
                "answerable": True,
                "required_evidence_ids": ["RESET"],
            },
            {
                "question_id": "U",
                "question": "Where is the secret code?",
                "split": split,
                "answerable": False,
            },
        ],
    }
    path = tmp_path / "reviewed.json"
    path.write_text(json.dumps(value))
    return path


def test_portable_reviewed_metrics_and_denominators_reconcile_with_reports(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Hold reset for eight seconds.")
    snapshot = load_corpus(source, exclude=[])
    labels = reviewed_file(tmp_path, snapshot)
    result = run_portable(
        source,
        [],
        StrategyConfig(name="bm25", strategy="bm25", k=1),
        output_root=tmp_path / "out",
        reviewed_file=labels,
        formats=["json", "html", "markdown"],
    )
    evaluation = result.report["evaluation"]
    assert result.report["evaluation_level"] == "reviewed_evaluation"
    assert evaluation["scope"] == "exact_returned_spans"
    q, unanswerable = evaluation["questions"]
    assert q["sufficient_evidence"] is True and q["evidence_coverage"] == 1
    assert q["reciprocal_rank"] == 1 and q["precision_at_k"] == 1
    assert unanswerable["sufficient_evidence"] is None
    assert evaluation["summaries"]["dev"]["answerable_questions"] == 1
    assert evaluation["summaries"]["heldout"]["sufficiency_rate"] is None
    assert json.loads((result.directory / "evaluation.json").read_text()) == evaluation
    for name in ("report.html", "report.md"):
        assert "Sufficient evidence" in (result.directory / name).read_text()
        assert "Sufficient evidence: N/A" in (result.directory / name).read_text()
        assert "Stage evidence" in (result.directory / name).read_text()


@pytest.mark.parametrize(
    "change,reason",
    [
        (lambda value: value.update(corpus_hash="changed"), "corpus hash"),
        (
            lambda value: value["evidence"][0]["spans"][0].update(text="wrong", end=20),
            "offsets|quote",
        ),
        (lambda value: value["evidence"].append(value["evidence"][0]), "unique"),
        (lambda value: value["questions"][0].update(required_evidence_ids=["UNKNOWN"]), "unknown"),
    ],
)
def test_reviewed_inputs_fail_before_run_directory(tmp_path, change, reason):
    source = tmp_path / "manual.txt"
    source.write_text("Hold reset for eight seconds.")
    snapshot = load_corpus(source, exclude=[])
    labels = reviewed_file(tmp_path, snapshot)
    value = json.loads(labels.read_text())
    change(value)
    labels.write_text(json.dumps(value))
    with pytest.raises(ValueError, match=reason):
        run_portable(
            source,
            [],
            StrategyConfig(name="bm25", strategy="bm25"),
            output_root=tmp_path / "out",
            reviewed_file=labels,
        )
    assert not (tmp_path / "out").exists()


def test_hand_calculated_prefix_completion_rank_and_coverage():
    references = ReviewedReferences(
        corpus_hash="fixture",
        evidence=[
            EvidenceItem(
                evidence_id="E", spans=[{"source_id": "D", "start": 2, "end": 8, "text": "234567"}]
            ),
            EvidenceItem(
                evidence_id="MISSING",
                spans=[{"source_id": "OTHER", "start": 0, "end": 2, "text": "01"}],
            ),
        ],
        questions=[
            {
                "question_id": "Q",
                "question": "number",
                "split": "heldout",
                "answerable": True,
                "required_evidence_ids": ["E", "MISSING"],
            }
        ],
    )
    contexts = [passage(0, 5), passage(5, 10)]
    config = StrategyConfig(name="fixture", strategy="bm25", k=2)
    manifest = build_manifest(
        [], [], config, dataset_hash="fixture", evaluation_level="reviewed_evaluation"
    )
    run = ExperimentRun(
        manifest=manifest,
        queries=[
            QueryRun(
                question_id="Q",
                hits=[
                    RetrievalHit(source_unit_id=p.source_unit_id, rank=i, score=1.0)
                    for i, p in enumerate(contexts, 1)
                ],
                context=contexts,
                query_time_ms=1,
            )
        ],
    )
    row = score_spans(run, references)["questions"][0]
    assert row["sufficient_evidence"] is False
    assert row["evidence_coverage"] == 0.5
    assert row["reciprocal_rank"] == 0.5
    assert row["precision_at_k"] == 1
    assert row["found_evidence_ids"] == ["E"]


def test_portable_validation_rejects_forged_context_hash_and_missing_questions(tmp_path):
    source = tmp_path / "manual.txt"
    source.write_text("Reset eight seconds")
    snapshot = load_corpus(source, exclude=[])
    result = run_portable(
        source,
        [SearchQuestion(question_id="Q", question="reset")],
        StrategyConfig(name="bm25", strategy="bm25"),
        output_root=tmp_path / "out",
    )
    run = ExperimentRun.model_validate_json((result.directory / "run.json").read_text())
    run.queries[0].context_hash = content_hash("forged")
    with pytest.raises(ValueError, match="hash"):
        validate_portable_run(snapshot, [SearchQuestion(question_id="Q", question="reset")], run)
    run.queries = []
    with pytest.raises(ValueError, match="each question"):
        validate_portable_run(snapshot, [SearchQuestion(question_id="Q", question="reset")], run)
