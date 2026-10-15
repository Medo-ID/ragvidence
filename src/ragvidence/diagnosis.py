"""Small evidence-backed diagnostic rules for the guided comparison."""

from typing import Any


def diagnose(comparison: dict[str, Any]) -> dict[str, str]:
    summary = comparison["summary"]
    before = comparison.get("baseline", {})
    after = comparison.get("intervention", {})
    ignored = {"name", "representation"}
    heading_only = (
        before.get("representation") == "body"
        and after.get("representation") == "heading_context"
        and {key: value for key, value in before.items() if key not in ignored}
        == {key: value for key, value in after.items() if key not in ignored}
    )
    if summary["fail_to_pass"] and not summary["pass_to_fail"]:
        return {
            "pattern": (
                "Missing structural context in the baseline representation"
                if heading_only
                else "Retrieval intervention improved evidence sufficiency"
            ),
            "evidence": (
                f"{summary['fail_to_pass']} failed queries passed after the intervention "
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
            "pattern": "Retrieval intervention introduced regressions",
            "evidence": f"{summary['pass_to_fail']} previously successful queries now fail.",
            "next_experiment": "Inspect regressed queries before adopting the intervention.",
            "confidence": "high",
            "limit": "The rule does not identify the underlying ranking mechanism.",
        }
    return {
        "pattern": "No clear retrieval benefit at the selected depth",
        "evidence": "The comparison contains no clean fail-to-pass signal.",
        "next_experiment": (
            "Inspect failures and test a different diagnosed intervention without changing labels."
        ),
        "confidence": "medium",
        "limit": "Results apply only to this dataset, strategy and retrieval depth.",
    }
