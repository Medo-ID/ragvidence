"""Shared summaries with explicit denominators and paired cluster uncertainty."""

from collections import defaultdict

import numpy as np

METRICS = {
    "sufficiency_rate": "sufficient_evidence",
    "mean_evidence_coverage": "evidence_coverage",
    "mean_reciprocal_rank": "reciprocal_rank",
    "mean_precision_at_k": "precision_at_k",
}


def summarize(rows: list[dict]) -> dict:
    answerable = [row for row in rows if row["answerable"]]
    count = len(answerable)
    return {
        "question_count": len(rows),
        "answerable_questions": count,
        "sufficient_count": sum(row["sufficient_evidence"] for row in answerable),
        **{
            name: sum(row[key] for row in answerable) / count if count else None
            for name, key in METRICS.items()
        },
    }


def paired_interval(
    differences: list[float],
    groups: list[str],
    *,
    seed: int,
    samples: int,
) -> dict:
    if len(differences) != len(groups):
        raise ValueError("Paired differences and groups must align")
    clustered = defaultdict(list)
    for difference, group in zip(differences, groups, strict=True):
        clustered[group].append(difference)
    count = len(clustered)
    result = {
        "estimate": float(np.mean(differences)) if differences else None,
        "question_count": len(differences),
        "group_count": count,
        "lower": None,
        "upper": None,
        "seed": seed,
        "samples": samples,
        "method": "paired-cluster-percentile-bootstrap-v1",
        "numpy_version": np.__version__,
        "confidence": 0.95,
        "note": "No interval: fewer than two independent declared groups",
    }
    if count < 2:
        return result
    totals = np.asarray([sum(values) for values in clustered.values()])
    sizes = np.asarray([len(values) for values in clustered.values()])
    rng = np.random.default_rng(seed)
    # Bound memory regardless of group/question counts.
    draws = []
    for _ in range(samples):
        indexes = rng.integers(0, count, count)
        draws.append(float(totals[indexes].sum() / sizes[indexes].sum()))
    result.update(
        lower=float(np.quantile(draws, 0.025)),
        upper=float(np.quantile(draws, 0.975)),
        note="Small samples and reused public heldout data limit inference"
        if count < 20
        else "Assumes declared groups are independent; intervals are descriptive after exploration",
    )
    return result
