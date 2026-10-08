import pytest

from ragvidence.evaluation.metrics import (
    classify_change,
    evidence_coverage_at_k,
    first_relevant_rank,
    precision_at_k,
    reciprocal_rank,
    sufficient_evidence_at_k,
)


def test_single_required_evidence_at_rank_one() -> None:
    ranking = [{"E-1"}, {"E-2"}]

    assert sufficient_evidence_at_k({"E-1"}, ranking, 2) is True
    assert evidence_coverage_at_k({"E-1"}, ranking, 2) == 1.0
    assert first_relevant_rank({"E-1"}, ranking, 2) == 1
    assert reciprocal_rank({"E-1"}, ranking, 2) == 1.0
    assert precision_at_k({"E-1"}, ranking, 2) == 0.5


def test_multi_evidence_requires_union_across_hits() -> None:
    ranking = [{"E-1"}, {"E-2"}, {"E-3"}]

    assert sufficient_evidence_at_k({"E-1", "E-2"}, ranking, 2) is True
    assert evidence_coverage_at_k({"E-1", "E-2"}, ranking, 1) == 0.5


def test_k_truncates_the_ranking() -> None:
    ranking = [{"OTHER"}, {"E-1"}]

    assert sufficient_evidence_at_k({"E-1"}, ranking, 1) is False
    assert evidence_coverage_at_k({"E-1"}, ranking, 1) == 0.0
    assert first_relevant_rank({"E-1"}, ranking, 1) is None
    assert reciprocal_rank({"E-1"}, ranking, 1) == 0.0


def test_duplicate_evidence_is_counted_once_for_coverage() -> None:
    ranking = [{"E-1"}, {"E-1"}]

    assert evidence_coverage_at_k({"E-1", "E-2"}, ranking, 2) == 0.5


def test_one_hit_with_multiple_evidence_items_can_be_sufficient() -> None:
    ranking = [{"E-1", "E-2"}, {"OTHER"}]

    assert sufficient_evidence_at_k({"E-1", "E-2"}, ranking, 1) is True
    assert precision_at_k({"E-1", "E-2"}, ranking, 2) == 0.5


def test_unanswerable_metrics_are_undefined() -> None:
    ranking = [{"E-1"}]

    assert sufficient_evidence_at_k(set(), ranking, 1) is None
    assert evidence_coverage_at_k(set(), ranking, 1) is None
    assert first_relevant_rank(set(), ranking, 1) is None
    assert reciprocal_rank(set(), ranking, 1) is None
    assert precision_at_k(set(), ranking, 1) is None


@pytest.mark.parametrize("k", [0, -1])
def test_metrics_reject_non_positive_k(k: int) -> None:
    functions = [
        sufficient_evidence_at_k,
        evidence_coverage_at_k,
        first_relevant_rank,
        reciprocal_rank,
        precision_at_k,
    ]

    for function in functions:
        with pytest.raises(ValueError, match="k must be positive"):
            function({"E-1"}, [{"E-1"}], k)


def test_precision_uses_k_as_the_denominator() -> None:
    assert precision_at_k({"E-1"}, [{"E-1"}], 3) == pytest.approx(1 / 3)


@pytest.mark.parametrize(
    ("baseline", "intervention", "expected"),
    [
        (False, True, "fail_to_pass"),
        (True, False, "pass_to_fail"),
        (True, True, "pass_to_pass"),
        (False, False, "fail_to_fail"),
    ],
)
def test_classify_change(
    baseline: bool,
    intervention: bool,
    expected: str,
) -> None:
    assert classify_change(baseline, intervention) == expected
