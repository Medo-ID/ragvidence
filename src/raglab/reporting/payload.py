"""Build one authoritative, share-safe report payload."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from raglab.comparison import compare_evaluations
from raglab.diagnosis import diagnose


def build_report(
    baseline: dict[str, Any], intervention: dict[str, Any] | None = None
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "baseline": baseline,
        "intervention": intervention,
        "comparison": None,
        "diagnosis": None,
        "limitations": [
            "Constructed teaching data and a small reviewed question set.",
            "Retrieval evaluation does not prove generated-answer correctness.",
            "Results apply to the recorded strategy, representation, dataset and k.",
        ],
    }
    if intervention is not None:
        comparison = compare_evaluations(baseline, intervention)
        report["comparison"] = comparison
        report["diagnosis"] = diagnose(comparison)
    return report
