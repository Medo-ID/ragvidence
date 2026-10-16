"""Revalidate saved runs and all derived evaluation facts before reuse."""

from pathlib import Path

from ragvidence.artifacts import content_hash
from ragvidence.evaluation.spans import score_spans
from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import ExperimentRun, SearchQuestion, SourceUnit
from ragvidence.portable_validation import validate_portable_run
from ragvidence.reporting.inspection import build_inspection_report
from ragvidence.reviewed import ReviewedReferences
from ragvidence.suites.models import FrozenJob, FrozenSuite
from ragvidence.suites.preparation import effective_config
from ragvidence.suites.storage import file_digest, member, read_json, verify_checkpoint


def load_frozen(root: Path):
    plan = FrozenSuite.model_validate(read_json(root / "suite.json"))
    if read_json(root / "plan-hash.json") != {"hash": content_hash(plan)}:
        raise ValueError("Frozen suite plan identity mismatch")
    for relative, digest in plan.files.items():
        if file_digest(member(root, relative)) != digest:
            raise ValueError(f"Frozen input changed: {relative}")
    snapshot = CorpusSnapshot.model_validate(read_json(root / "snapshot.json"))
    questions = [
        SearchQuestion.model_validate(value) for value in read_json(root / "questions.json")
    ]
    references = (
        ReviewedReferences.model_validate(read_json(root / "references.json"))
        if plan.references_hash
        else None
    )
    if (
        content_hash(snapshot) != plan.snapshot_hash
        or content_hash(questions) != plan.questions_hash
    ):
        raise ValueError("Frozen suite snapshot/questions do not match plan")
    if references:
        references.validate_snapshot(snapshot)
        if references.identity != plan.references_hash:
            raise ValueError("Frozen reference identity mismatch")
    return plan, snapshot, questions, references


def validate_completed(directory: Path, snapshot, questions, references, job: FrozenJob) -> dict:
    verify_checkpoint(directory)
    run = ExperimentRun.model_validate(read_json(directory / "run.json"))
    config = effective_config(job, questions)
    if run.manifest.config != config:
        raise ValueError("Checkpoint configuration differs from frozen suite")
    sources = [
        SourceUnit.model_validate(value) for value in read_json(directory / "search-sources.json")
    ]
    validate_portable_run(
        snapshot, questions, run, references.identity if references else None, sources
    )
    report = read_json(directory / "report.json")
    if references:
        evaluation = score_spans(run, references)
        saved = read_json(directory / "evaluation.json")
        proxy = any("ID-only results" in warning for warning in run.manifest.warnings)
        evaluation["scope"] = "registered_unit_proxy" if proxy else "exact_returned_spans"
        if saved != evaluation or report.get("evaluation") != evaluation:
            raise ValueError("Saved comparison evaluation does not match its run")
    expected = build_inspection_report(
        snapshot,
        questions,
        run,
        name=report["input"]["name"],
        evaluation=evaluation if references else None,
    )
    expected.pop("generated_at")
    actual = dict(report)
    actual.pop("generated_at")
    if expected != actual:
        raise ValueError("Saved report facts differ from validated run/evaluation")
    return report
