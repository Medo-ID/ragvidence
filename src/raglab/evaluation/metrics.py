"""Pure evidence-level retrieval metrics.

These pure functions are shared by every retrieval strategy.
Do not add file I/O, model calls, logging, or framework dependencies here.
"""

from collections.abc import Collection, Sequence

from raglab.models import ChangeClassification

EvidenceRanking = Sequence[Collection[str]]


def sufficient_evidence_at_k(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> bool | None:
    """Return whether all required evidence occurs in the first k hits.

    Return None when required_evidence is empty because retrieval success is not
    defined for an unanswerable question.
    """
    if k <= 0:
        raise ValueError("k must be positive")

    if not required_evidence:
        return None

    found_evidence: set[str] = set()
    for hit_evidence in retrieved_evidence[:k]:
        found_evidence.update(hit_evidence)

    return set(required_evidence).issubset(found_evidence)


def evidence_coverage_at_k(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return the fraction of unique required evidence found in the first k hits."""
    if k <= 0:
        raise ValueError("k must be positive")

    if not required_evidence:
        return None

    required = set(required_evidence)
    found_evidence: set[str] = set()
    for hit_evidence in retrieved_evidence[:k]:
        found_evidence.update(hit_evidence)

    found_required_evidence = required.intersection(found_evidence)
    return len(found_required_evidence) / len(required)


def first_relevant_rank(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> int | None:
    """Return the one-based first relevant rank within k, or None when absent/undefined."""
    if k <= 0:
        raise ValueError("k must be positive")

    if not required_evidence:
        return None

    required = set(required_evidence)
    for rank, hit_evidence in enumerate(retrieved_evidence[:k], start=1):
        if required.intersection(hit_evidence):
            return rank

    return None


def reciprocal_rank(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return 1/rank, 0.0 for no relevant hit, or None for unanswerable questions."""
    if k <= 0:
        raise ValueError("k must be positive")

    if not required_evidence:
        return None

    rank = first_relevant_rank(required_evidence, retrieved_evidence, k)
    if rank is None:
        return 0.0

    return 1.0 / rank


def precision_at_k(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return relevant hits divided by k, or None for unanswerable questions."""
    if k <= 0:
        raise ValueError("k must be positive")

    if not required_evidence:
        return None

    required = set(required_evidence)
    relevant_hits = 0
    for hit_evidence in retrieved_evidence[:k]:
        if required.intersection(hit_evidence):
            relevant_hits += 1

    return relevant_hits / k


def classify_change(
    baseline_success: bool,
    intervention_success: bool,
) -> ChangeClassification:
    """Classify how a question changed between two retrieval runs."""
    mapping: dict[tuple[bool, bool], ChangeClassification] = {
        (False, True): "fail_to_pass",
        (True, False): "pass_to_fail",
        (True, True): "pass_to_pass",
        (False, False): "fail_to_fail",
    }

    state = (baseline_success, intervention_success)
    return mapping[state]
