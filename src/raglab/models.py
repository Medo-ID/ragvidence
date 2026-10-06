"""Validated data contracts shared by retrieval, evaluation, and reporting."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class SourceUnit(StrictModel):
    """A stable, human-inspectable unit of source evidence."""

    source_unit_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    body: str = Field(min_length=1)
    evidence_ids: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionCase(StrictModel):
    """A reviewed retrieval-evaluation question."""

    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    split: Literal["dev", "heldout"]
    answerable: bool
    required_evidence_ids: set[str] = Field(default_factory=set)
    reference_answer: str | None = None
    tags: set[str] = Field(default_factory=set)

    @model_validator(mode="after")
    def validate_answerability(self) -> "QuestionCase":
        if self.answerable and not self.required_evidence_ids:
            raise ValueError("answerable questions require at least one evidence ID")
        if not self.answerable and self.required_evidence_ids:
            raise ValueError("unanswerable questions cannot require evidence IDs")
        return self


class RetrievalHit(StrictModel):
    """One ranked retrieval result."""

    source_unit_id: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float
    evidence_ids: set[str] = Field(default_factory=set)
    preview: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


ChangeClassification = Literal[
    "fail_to_pass",
    "pass_to_fail",
    "pass_to_pass",
    "fail_to_fail",
]


class StrategyConfig(StrictModel):
    """One reproducible retrieval configuration."""

    name: str = Field(min_length=1)
    strategy: Literal["bm25", "semantic", "imported"]
    representation: Literal["body", "heading_context"] = "body"
    k: int = Field(default=2, ge=1)
    model: str | None = None
    provider: Literal["fastembed", "ollama", "openai_compatible"] | None = None


class QueryRun(StrictModel):
    """Ranked output for one question under one strategy."""

    question_id: str
    hits: list[RetrievalHit]
    query_time_ms: float = Field(ge=0)


class RunManifest(StrictModel):
    """Metadata required to reproduce a run."""

    run_id: str
    created_at: str
    product_version: str
    python_version: str
    platform: str
    dataset_hash: str
    config: StrategyConfig
    index_time_ms: float = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class ExperimentRun(StrictModel):
    """Authoritative retrieval-run artifact."""

    manifest: RunManifest
    queries: list[QueryRun]
