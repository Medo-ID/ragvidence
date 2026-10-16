"""Reviewed references anchor to frozen originals, independently of chunk IDs."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ragvidence.artifacts import content_hash
from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import QuestionCase, StrictModel


class EvidenceSpan(StrictModel):
    source_id: str = Field(min_length=1)
    start: int = Field(ge=0, strict=True)
    end: int = Field(ge=1, strict=True)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def exact_length(self):
        if self.end - self.start != len(self.text):
            raise ValueError("Evidence offsets must describe the exact quoted text")
        return self


class EvidenceItem(StrictModel):
    evidence_id: str = Field(min_length=1)
    spans: list[EvidenceSpan] = Field(min_length=1)


class ReviewedReferences(StrictModel):
    schema_version: Literal[1] = 1
    corpus_hash: str
    evidence: list[EvidenceItem]
    questions: list[QuestionCase] = Field(min_length=1)

    @property
    def identity(self) -> str:
        return content_hash(self)

    def validate_snapshot(self, snapshot: CorpusSnapshot) -> None:
        if self.corpus_hash != snapshot.corpus_hash:
            raise ValueError("Reviewed references do not match the frozen corpus hash")
        documents = {document.source_unit_id: document for document in snapshot.documents}
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Reviewed evidence IDs must be unique")
        questions = [item.question_id for item in self.questions]
        if len(questions) != len(set(questions)):
            raise ValueError("Reviewed question IDs must be unique")
        for item in self.evidence:
            for span in item.spans:
                source = documents.get(span.source_id)
                if source is None or source.body[span.start : span.end] != span.text:
                    raise ValueError(
                        f"Evidence {item.evidence_id}: source/quote/offsets do not match"
                    )
        for question in self.questions:
            if question.required_evidence_ids - set(ids):
                raise ValueError(f"{question.question_id}: unknown required evidence IDs")


def load_reviewed(path: Path, snapshot: CorpusSnapshot) -> ReviewedReferences:
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Reviewed references exceed 10 MiB")
    references = ReviewedReferences.model_validate_json(path.read_text(encoding="utf-8"))
    references.validate_snapshot(snapshot)
    return references
