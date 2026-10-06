"""Compare evaluated runs without hiding regressions."""

from typing import Any

from raglab.evaluation.metrics import classify_change


def compare_evaluations(baseline: dict[str, Any], intervention: dict[str, Any]) -> dict[str, Any]:
    baseline_manifest = baseline["manifest"]
    intervention_manifest = intervention["manifest"]
    if baseline_manifest["dataset_hash"] != intervention_manifest["dataset_hash"]:
        raise ValueError("Runs use different dataset hashes")
    baseline_k = baseline_manifest["config"]["k"]
    intervention_k = intervention_manifest["config"]["k"]
    if baseline_k != intervention_k:
        raise ValueError("Runs use different retrieval depths (k)")
    before = {item["question_id"]: item for item in baseline["questions"]}
    after = {item["question_id"]: item for item in intervention["questions"]}
    if before.keys() != after.keys():
        raise ValueError("Runs contain different question IDs")
    changes = []
    for question_id in sorted(before):
        old = before[question_id]["sufficient_evidence"]
        new = after[question_id]["sufficient_evidence"]
        status = None if old is None or new is None else classify_change(old, new)
        changes.append({"question_id": question_id, "classification": status})
    return {
        "baseline": baseline["manifest"]["config"],
        "intervention": intervention["manifest"]["config"],
        "summary": {
            key: sum(item["classification"] == key for item in changes)
            for key in ("fail_to_pass", "pass_to_fail", "pass_to_pass", "fail_to_fail")
        },
        "changes": changes,
    }
