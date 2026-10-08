"""Small evidence-backed diagnostic rules for the guided comparison."""

from typing import Any


def diagnose(comparison: dict[str, Any]) -> dict[str, str]:
    summary = comparison["summary"]
    if summary["fail_to_pass"] and not summary["pass_to_fail"]:
        return {
            "pattern": "Missing structural context in the baseline representation",
            "evidence": (
                f"{summary['fail_to_pass']} failed queries passed after enrichment "
                "with no regressions."
            ),
            "next_experiment": (
                "Repeat on a frozen slice of your own corpus and inspect every changed rank."
            ),
            "confidence": "medium",
            "limit": (
                "This rule identifies correlation in a small labeled comparison, "
                "not universal causation."
            ),
        }
    if summary["pass_to_fail"]:
        return {
            "pattern": "Representation change introduced retrieval regressions",
            "evidence": f"{summary['pass_to_fail']} previously successful queries now fail.",
            "next_experiment": "Inspect regressed queries before adopting the intervention.",
            "confidence": "high",
            "limit": "The rule does not identify the underlying ranking mechanism.",
        }
    return {
        "pattern": "No clear heading-context benefit at the selected depth",
        "evidence": "The comparison contains no clean fail-to-pass signal.",
        "next_experiment": (
            "Inspect failures and test a different diagnosed intervention without changing labels."
        ),
        "confidence": "medium",
        "limit": "Results apply only to this dataset, strategy and retrieval depth.",
    }
