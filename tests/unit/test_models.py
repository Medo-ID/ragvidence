import pytest
from pydantic import ValidationError

from raglab.models import QuestionCase


def test_answerable_question_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        QuestionCase(
            question_id="Q-1",
            question="What is the reset duration?",
            split="dev",
            answerable=True,
        )


def test_unanswerable_question_rejects_required_evidence() -> None:
    with pytest.raises(ValidationError):
        QuestionCase(
            question_id="Q-2",
            question="What is the warranty?",
            split="heldout",
            answerable=False,
            required_evidence_ids={"E-1"},
        )
