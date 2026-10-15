"""Build one authoritative, share-safe report payload."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ragvidence.comparison import compare_evaluations
from ragvidence.diagnosis import diagnose
from ragvidence.evaluation.validation import validate_evaluation


def build_report(
    baseline: dict[str, Any], intervention: dict[str, Any] | None = None
) -> dict[str, Any]:
    validate_evaluation(baseline)
    if intervention is not None:
        validate_evaluation(intervention)
    for evaluation in [baseline, *([intervention] if intervention is not None else [])]:
        summary = evaluation.get("summary")
        if not isinstance(summary, dict) or not {
            "successful",
            "answerable",
            "sufficient_evidence_rate",
        }.issubset(summary):
            raise ValueError("Report input requires a complete evaluation summary")
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "baseline": {key: value for key, value in baseline.items() if key != "_validation"},
        "intervention": (
            {key: value for key, value in intervention.items() if key != "_validation"}
            if intervention is not None
            else None
        ),
        "comparison": None,
        "diagnosis": None,
        "limitations": [
            "Conclusions apply to the provided corpus and reviewed question set.",
            "Retrieval evaluation does not prove generated-answer correctness.",
            "Results apply to the recorded strategy, representation, dataset and k.",
        ],
    }
    if baseline.get("schema_version", 1) == 1 or (
        intervention is not None and intervention.get("schema_version", 1) == 1
    ):
        report["limitations"].append(
            "Legacy evaluation: complete source/run provenance was not recorded."
        )
    if intervention is not None:
        comparison = compare_evaluations(baseline, intervention)
        report["comparison"] = comparison
        report["diagnosis"] = diagnose(comparison)
    return report
