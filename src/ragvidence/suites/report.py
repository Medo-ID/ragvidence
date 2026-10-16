"""Compute comparison facts once; renderers never calculate metrics or winners."""

import json
from datetime import UTC, datetime

from ragvidence.evaluation.aggregation import METRICS, paired_interval, summarize
from ragvidence.suites.models import Criteria, FrozenSuite
from ragvidence.suites.resources import resources as measured_resources


def criterion_matches(summary: dict | None, resources: dict, criteria: Criteria) -> dict:
    checks = []
    for name, limit in criteria.model_dump().items():
        if limit is None or name == "context_unit":
            continue
        if name == "min_sufficiency_rate":
            value = summary["sufficiency_rate"] if summary else None
            matches = value >= limit if value is not None else None
        else:
            measurement = resources["query_ms" if name == "max_mean_query_ms" else "context_units"]
            value = measurement["mean_known"] if not measurement["missing_count"] else None
            if (
                name == "max_mean_context_units"
                and resources.get("context_unit") != criteria.context_unit
            ):
                value = None
            matches = value <= limit if value is not None else None
        checks.append({"criterion": name, "limit": limit, "observed": value, "matches": matches})
    return {
        "status": "not_requested"
        if not checks
        else "not_matched"
        if any(check["matches"] is False for check in checks)
        else "unknown"
        if any(check["matches"] is None for check in checks)
        else "matched",
        "checks": checks,
    }


def _groups(rows: list[dict], declared: dict[str, str]) -> list[str]:
    groups = []
    for row in rows:
        if row["question_id"] in declared:
            groups.append(
                json.dumps(["group", declared[row["question_id"]].removeprefix("family:")])
            )
            continue
        tags = [tag for tag in row["tags"] if tag.startswith("family:")]
        if len(tags) > 1:
            raise ValueError("Question may declare only one family: group tag")
        groups.append(
            json.dumps(["group", tags[0].removeprefix("family:")])
            if tags
            else json.dumps(["question", row["question_id"]])
        )
    return groups


def _compare(baseline: dict, participant: dict, plan: FrozenSuite) -> dict:
    left = baseline["report"]
    right = participant["report"]
    rows = []
    aggregates = {}
    if left.get("evaluation") and right.get("evaluation"):
        by_id = {row["question_id"]: row for row in left["evaluation"]["questions"]}
        for row in right["evaluation"]["questions"]:
            before = by_id[row["question_id"]]
            change = None
            if row["answerable"]:
                change = {
                    (False, True): "improved",
                    (True, False): "regressed",
                    (True, True): "stable_pass",
                    (False, False): "stable_fail",
                }[(before["sufficient_evidence"], row["sufficient_evidence"])]
            rows.append(
                {
                    "question_id": row["question_id"],
                    "split": row["split"],
                    "tags": row["tags"],
                    "answerable": row["answerable"],
                    "change": change,
                    "gained": sorted(
                        set(row["found_evidence_ids"]) - set(before["found_evidence_ids"])
                    ),
                    "lost": sorted(
                        set(before["found_evidence_ids"]) - set(row["found_evidence_ids"])
                    ),
                    "missing": row["missing_evidence_ids"],
                    "deltas": {
                        metric: float(row[key]) - float(before[key]) if row["answerable"] else None
                        for metric, key in METRICS.items()
                    },
                }
            )
        scopes = {"all": [], **plan.spec.slices}
        for split in ("dev", "heldout"):
            aggregates[split] = {}
            for name, tags in scopes.items():
                subset = [
                    row
                    for row in rows
                    if row["split"] == split and row["answerable"] and set(tags) <= set(row["tags"])
                ]
                groups = _groups(subset, plan.spec.question_groups)
                aggregates[split][name] = {
                    "answerable_questions": len(subset),
                    "changes": {
                        change: sum(row["change"] == change for row in subset)
                        for change in ("improved", "regressed", "stable_pass", "stable_fail")
                    },
                    "intervals": {
                        metric: paired_interval(
                            [row["deltas"][metric] for row in subset],
                            groups,
                            seed=plan.spec.bootstrap_seed,
                            samples=plan.spec.bootstrap_samples,
                        )
                        for metric in METRICS
                    },
                }
    exact = bool(
        left.get("evaluation")
        and right.get("evaluation")
        and left["evaluation"]["scope"] == right["evaluation"]["scope"] == "exact_returned_spans"
    )
    return {
        "baseline": baseline["name"],
        "participant": participant["name"],
        "quality_comparable": exact,
        "scope": "exact_returned_spans" if exact else "proxy_or_unscored",
        "questions": rows,
        "splits": aggregates,
        "interpretation": "Observed gains/losses under the declared policy; no automatic winner"
        if exact
        else "ID proxies or missing references prevent an actual-context quality recommendation",
    }


def build_comparison(plan: FrozenSuite, entries: list[dict], *, resumed: bool) -> dict:
    participants = []
    for entry in entries:
        entry = dict(entry)
        if entry["state"] == "complete":
            evaluation = entry["report"].get("evaluation")
            entry["evidence_scope"] = (
                evaluation["scope"] if evaluation else entry["report"]["evaluation_level"]
            )
            scopes = {"all": [], **plan.spec.slices}
            entry["summaries"] = (
                {
                    split: {
                        name: summarize(
                            [
                                row
                                for row in evaluation["questions"]
                                if row["split"] == split and set(tags) <= set(row["tags"])
                            ]
                        )
                        for name, tags in scopes.items()
                    }
                    for split in ("dev", "heldout")
                }
                if evaluation
                else {}
            )
            entry["split_resources"] = (
                {
                    split: measured_resources(
                        {
                            **entry["report"],
                            "questions": [
                                question
                                for question in entry["report"]["questions"]
                                if question["question_id"]
                                in {
                                    row["question_id"]
                                    for row in evaluation["questions"]
                                    if row["split"] == split
                                }
                            ],
                        }
                    )
                    for split in ("dev", "heldout")
                }
                if evaluation
                else {}
            )
            entry["criteria"] = (
                {
                    split: criterion_matches(
                        entry["summaries"][split]["all"]
                        if entry["evidence_scope"] == "exact_returned_spans"
                        else None,
                        entry["split_resources"][split],
                        plan.spec.criteria,
                    )
                    for split in entry["summaries"]
                }
                if evaluation
                else {"inspection": criterion_matches(None, entry["resources"], plan.spec.criteria)}
            )
        participants.append(entry)
    baseline = next(
        (
            entry
            for entry in participants
            if entry["name"] == plan.baseline and entry["state"] == "complete"
        ),
        None,
    )
    comparisons = [
        _compare(baseline, entry, plan)
        for entry in participants
        if baseline and entry["state"] == "complete" and entry["name"] != baseline["name"]
    ]
    failed = any(entry["state"] != "complete" for entry in participants)
    labeled = any(entry.get("report", {}).get("evaluation") for entry in participants)
    return {
        "schema_version": 1,
        "kind": "comparison",
        "generated_at": datetime.now(UTC).isoformat(),
        "state": "partial_failure" if failed else "complete",
        "input_name": plan.input_name,
        "evaluation_level": "reviewed_comparison" if labeled else "unscored_comparison",
        "policy": plan.spec.policy,
        "baseline": plan.baseline,
        "phase": plan.phase,
        "resumed": resumed,
        "heldout_use": plan.heldout_use,
        "query_call_upper_bound": plan.query_call_upper_bound,
        "participants": participants,
        "comparisons": comparisons,
        "observations": [
            "Keeping the baseline is valid. Choose using these cases and your requirements.",
            "Equal k does not imply equal context volume; resources are reported separately.",
            "Unlabeled data cannot establish a quality winner."
            if not labeled
            else "Intervals pair questions or families. Repeated timings are not extra samples.",
            "No valid baseline comparison is available."
            if baseline is None
            else "These observations do not prove what caused a particular failure.",
        ],
        "limitations": [
            "Grids are exploratory. Intervals are not adjusted for multiple comparisons.",
            "Heldout reuse is tracked under this output root, without protection against edits.",
            "Vector reuse is observed. Model/OS cache warmth and external traces are unknown.",
            "Missing timing/cost is unavailable. Supplied usage/pricing yields labeled estimates.",
            "nDCG requires graded relevance gains. Answer quality is not evaluated.",
        ],
    }
