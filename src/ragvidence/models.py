"""Validated data contracts shared by retrieval, evaluation, and reporting."""

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    field_validator,
    model_serializer,
    model_validator,
)


class StrictModel(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class SourceUnit(StrictModel):
    """A stable, human-inspectable unit of source evidence."""

    source_unit_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    body: str = Field(min_length=1)
    evidence_ids: set[str] = Field(default_factory=set)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchQuestion(StrictModel):
    """A search question whose expected evidence may be unknown."""

    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)

    @field_validator("question_id", "question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question text and ID cannot be blank")
        return value


class QuestionCase(SearchQuestion):
    """A reviewed retrieval-evaluation question, separate from exploration."""

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
    rank: int = Field(ge=1, strict=True)
    score: float = Field(strict=True)
    evidence_ids: set[str] = Field(default_factory=set)
    preview: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    context_spans: list["TextSpan"] | None = None

    @model_serializer(mode="wrap")
    def serialize_hit(self, handler):
        values = handler(self)
        if values.get("context_spans") is None:
            values.pop("context_spans", None)
        return values


class TextSpan(StrictModel):
    """Half-open character offsets relative to one retrieved source body."""

    start: int = Field(ge=0, strict=True)
    end: int = Field(ge=1, strict=True)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Text span end must exceed start")
        return self


MetadataScalar = StrictStr | StrictBool | StrictInt | StrictFloat | None


class MetadataPredicate(StrictModel):
    field: str = Field(min_length=1, max_length=256, pattern=r"^[^.]+(?:\.[^.]+)*$")
    op: Literal["eq", "in", "gt", "gte", "lt", "lte"]
    value: MetadataScalar | list[MetadataScalar]

    @model_validator(mode="after")
    def operand(self):
        if self.op == "in":
            if not isinstance(self.value, list) or not 1 <= len(self.value) <= 100:
                raise ValueError("Membership requires 1 to 100 scalar values")
        elif isinstance(self.value, list):
            raise ValueError("This predicate requires one scalar value")
        elif self.op != "eq" and type(self.value) not in {int, float, str}:
            raise ValueError("Range comparisons require a number or string")
        return self


class FilterConfig(StrictModel):
    all: list[MetadataPredicate] = Field(default_factory=list, max_length=32)
    questions: dict[str, list[MetadataPredicate]] = Field(default_factory=dict, max_length=10000)

    @model_validator(mode="after")
    def bounded(self):
        if any(not key or len(values) > 32 for key, values in self.questions.items()):
            raise ValueError("Question filters require IDs and at most 32 predicates")
        return self


class MMRConfig(StrictModel):
    lambda_mult: float = Field(default=0.5, ge=0, le=1)
    candidates: int = Field(default=20, ge=1, le=1000)


class RewriteConfig(StrictModel):
    model: str = Field(min_length=1, max_length=256)
    provider: Literal["ollama", "openai_compatible"] = "ollama"
    count: int = Field(default=3, ge=1, le=8, strict=True)
    max_output_tokens: int = Field(default=512, ge=32, le=4096, strict=True)
    timeout_seconds: float = Field(default=60, ge=1, le=300)
    include_original: bool = True
    failure: Literal["fail", "original"] = "fail"
    endpoint_hash: str | None = None
    prompt_version: Literal["query-rewrite-v1"] = "query-rewrite-v1"


class CompressionConfig(StrictModel):
    mode: Literal["sentences", "model"] = "sentences"
    max_spans: int = Field(default=2, ge=1, le=16, strict=True)
    max_output_tokens: int = Field(default=1024, ge=32, le=4096, strict=True)
    timeout_seconds: float = Field(default=60, ge=1, le=300)
    model: str | None = Field(default=None, min_length=1, max_length=256)
    provider: Literal["ollama", "openai_compatible"] = "ollama"
    failure: Literal["fail", "original"] = "fail"
    endpoint_hash: str | None = None
    prompt_version: Literal["extractive-spans-v1"] = "extractive-spans-v1"

    @model_validator(mode="after")
    def model_required(self):
        if self.mode == "model" and self.model is None:
            raise ValueError("Model compression requires a model")
        if self.mode == "sentences" and self.model is not None:
            raise ValueError("A compression model requires mode=model")
        return self


ChangeClassification = Literal[
    "fail_to_pass",
    "pass_to_fail",
    "pass_to_pass",
    "fail_to_fail",
]


class StrategyConfig(StrictModel):
    """One reproducible retrieval configuration."""

    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    strategy: Literal["bm25", "semantic", "hybrid", "imported"]
    representation: Literal["body", "heading_context", "contextual"] = "body"
    k: int = Field(default=2, ge=1)
    model: str | None = None
    provider: Literal["fastembed", "ollama", "openai_compatible"] | None = None
    candidate_k: int | None = Field(default=None, ge=1)
    lexical_weight: float = Field(default=0.5, gt=0, lt=1)
    rrf_constant: int = Field(default=60, ge=0)
    child_splitter: Literal["none", "recursive", "markdown"] = "none"
    child_size: int = Field(default=500, ge=1)
    child_overlap: int = Field(default=50, ge=0)
    query_variants: dict[str, list[str]] = Field(default_factory=dict)
    reranker_model: str | None = Field(default=None, min_length=1)
    branch_k: int | None = Field(default=None, ge=1)
    child_k: int | None = Field(default=None, ge=1)
    query_k: int | None = Field(default=None, ge=1)
    rerank_k: int | None = Field(default=None, ge=1)
    context_budget: int | None = Field(default=None, ge=1)
    tokenizer_file: str | None = None
    tokenizer_hash: str | None = None
    filters: FilterConfig | None = None
    mmr: MMRConfig | None = None
    rewrite: RewriteConfig | None = None
    compression: CompressionConfig | None = None

    @model_serializer(mode="wrap")
    def serialize_config(self, handler):
        values = handler(self)
        # Preserve identities of older configurations when new options are unused.
        for key in (
            "branch_k",
            "child_k",
            "query_k",
            "rerank_k",
            "context_budget",
            "tokenizer_file",
            "tokenizer_hash",
            "filters",
            "mmr",
            "rewrite",
            "compression",
        ):
            if values.get(key) is None:
                values.pop(key, None)
        return values

    @model_validator(mode="after")
    def validate_pipeline(self) -> "StrategyConfig":
        if self.strategy == "imported" and any(
            value is not None for value in (self.filters, self.mmr, self.rewrite, self.compression)
        ):
            raise ValueError("Imported results cannot execute retrieval transformations")
        if self.candidate_k is not None and self.candidate_k < self.k:
            raise ValueError("candidate_k must be at least k")
        if self.child_splitter != "none" and self.child_overlap >= self.child_size:
            raise ValueError("child_overlap must be smaller than child_size")
        for variants in self.query_variants.values():
            if any(not value.strip() for value in variants):
                raise ValueError("query variants must contain nonblank text")
            if len(variants) > 8:
                raise ValueError("At most eight supplied variants per question are supported")
        return self


class StageTrace(StrictModel):
    name: str
    elapsed_ms: float | None = Field(default=None, ge=0)
    hits: list[RetrievalHit] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class QueryRun(StrictModel):
    """Ranked output for one question under one strategy."""

    question_id: str
    hits: list[RetrievalHit]
    query_time_ms: float | None = Field(ge=0)
    search_queries: list[str] = Field(default_factory=list)
    returned_context_characters: int | None = Field(default=None, ge=0)
    context: list["ContextPassage"] = Field(default_factory=list)
    rendered_context: str | None = None
    context_hash: str | None = None
    stages: list[StageTrace] = Field(default_factory=list)
    context_measurement: dict[str, Any] = Field(default_factory=dict)


class ContextPassage(StrictModel):
    """Exact returned text and its offsets in an original source unit."""

    source_unit_id: str
    origin_source_id: str
    document_id: str
    start: int = Field(ge=0)
    end: int = Field(ge=1)
    text: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_offsets(self) -> "ContextPassage":
        if self.end - self.start != len(self.text):
            raise ValueError("Context offsets must describe the exact returned text")
        return self


class InputPreparation(StrictModel):
    """Materialization settings used before retrieval indexing."""

    implementation: Literal["portable-text-v1", "portable-files-v1"] = "portable-text-v1"
    length_unit: Literal["characters"] = "characters"
    chunk_size: int = Field(ge=1)
    chunk_overlap: int = Field(ge=0)
    text_field: str | None = None
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    limits: dict[str, int] = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def serialize_preparation(self, handler):
        data = handler(self)
        if self.implementation == "portable-text-v1":
            # Preserve identities of snapshots/runs written by the first portable release.
            for key in ("text_field", "include_patterns", "exclude_patterns", "limits"):
                data.pop(key, None)
        return data

    @model_validator(mode="after")
    def check_overlap(self) -> "InputPreparation":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size")
        if self.implementation == "portable-text-v1" and (
            self.text_field or self.include_patterns or self.exclude_patterns or self.limits
        ):
            raise ValueError("Extended ingestion settings require portable-files-v1")
        return self


class RunManifest(StrictModel):
    """Metadata required to reproduce a run."""

    run_id: str
    schema_version: Literal[1, 2] = 1
    hash_algorithm: Literal["legacy", "canonical-json-v1"] = "legacy"
    evaluation_level: Literal["ingestion_only", "retrieval_inspection", "reviewed_evaluation"] = (
        "reviewed_evaluation"
    )
    created_at: str
    product_version: str
    python_version: str
    platform: str
    dataset_hash: str
    corpus_hash: str | None = None
    questions_hash: str | None = None
    references_hash: str | None = None
    representation_hash: str | None = None
    configuration_hash: str | None = None
    input_preparation: InputPreparation | None = None
    config: StrategyConfig
    index_time_ms: float | None = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_hash_version(self) -> "RunManifest":
        if self.schema_version == 2 and self.hash_algorithm != "canonical-json-v1":
            raise ValueError("Version 2 runs require canonical-json-v1 hashing")
        return self


class ExperimentRun(StrictModel):
    """Authoritative retrieval-run artifact."""

    manifest: RunManifest
    queries: list[QueryRun]
