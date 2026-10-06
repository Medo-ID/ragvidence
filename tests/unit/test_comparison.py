import pytest

from raglab.comparison import compare_evaluations


def _evaluation(dataset_hash: str = "same", k: int = 2) -> dict:
    return {
        "manifest": {
            "dataset_hash": dataset_hash,
            "config": {"name": "run", "strategy": "bm25", "representation": "body", "k": k},
        },
        "questions": [{"question_id": "Q-1", "sufficient_evidence": True}],
    }


def test_comparison_rejects_dataset_drift_before_scoring() -> None:
    with pytest.raises(ValueError, match="dataset hashes"):
        compare_evaluations(_evaluation("a"), _evaluation("b"))


def test_comparison_rejects_different_k_before_scoring() -> None:
    with pytest.raises(ValueError, match="retrieval depths"):
        compare_evaluations(_evaluation(k=1), _evaluation(k=2))
