"""Pure evidence-level retrieval metrics.

Owner contribution: implement the functions below using the documented contract.
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
    raise NotImplementedError


def evidence_coverage_at_k(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return the fraction of unique required evidence found in the first k hits."""
    raise NotImplementedError


def first_relevant_rank(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> int | None:
    """Return the one-based first relevant rank within k, or None when absent/undefined."""
    raise NotImplementedError


def reciprocal_rank(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return 1/rank, 0.0 for no relevant hit, or None for unanswerable questions."""
    raise NotImplementedError


def precision_at_k(
    required_evidence: Collection[str],
    retrieved_evidence: EvidenceRanking,
    k: int,
) -> float | None:
    """Return relevant hits divided by k, or None for unanswerable questions."""
    raise NotImplementedError


def classify_change(
    baseline_success: bool,
    intervention_success: bool,
) -> ChangeClassification:
    """Classify how a question changed between two retrieval runs."""
    raise NotImplementedError
