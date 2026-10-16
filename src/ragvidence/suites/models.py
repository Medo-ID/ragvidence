"""Bounded declarative suites; no providers, files or reporting behavior."""

from itertools import product
from math import prod
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_serializer, model_validator

from ragvidence.capabilities import CAPABILITIES
from ragvidence.models import StrategyConfig, StrictModel


class Variant(StrictModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_-]+$", max_length=64)
    technique: str
    options: dict[str, Any] = Field(default_factory=dict)
    variants_file: Path | None = None
    prefixes_file: Path | None = None
    results_file: Path | None = None
    usage_file: Path | None = None
    filters_file: Path | None = None

    @model_serializer(mode="wrap")
    def serialize_variant(self, handler):
        values = handler(self)
        if values.get("filters_file") is None:
            values.pop("filters_file", None)
        return values

    @model_validator(mode="after")
    def known_technique(self):
        if self.technique not in {item.name for item in CAPABILITIES}:
            raise ValueError(f"Unknown portable technique: {self.technique}")
        return self


class Grid(StrictModel):
    variant: Variant
    axes: dict[str, list[Any]]

    @model_validator(mode="after")
    def nonempty_axes(self):
        if not self.axes or any(not values for values in self.axes.values()):
            raise ValueError("Grid axes must have at least one value")
        return self


class Criteria(StrictModel):
    min_sufficiency_rate: float | None = Field(default=None, ge=0, le=1)
    max_mean_query_ms: float | None = Field(default=None, ge=0)
    max_mean_context_units: float | None = Field(default=None, ge=0)
    context_unit: Literal["tokens", "characters"] | None = None

    @model_validator(mode="after")
    def context_units_are_explicit(self):
        if self.max_mean_context_units is not None and self.context_unit is None:
            raise ValueError("Context criteria require an explicit context_unit")
        return self


class Rate(StrictModel):
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(default=0, ge=0)


class Pricing(StrictModel):
    identity: str = Field(min_length=1)
    currency: str = Field(min_length=1)
    rates: dict[str, Rate]


class SuiteSpec(StrictModel):
    schema_version: Literal[1] = 1
    variants: list[Variant] = Field(default_factory=list)
    grids: list[Grid] = Field(default_factory=list)
    baseline: str | None = None
    policy: Literal["fixed_k", "fixed_tokens", "descriptive"] = "fixed_k"
    max_configurations: int = Field(default=16, ge=1, le=32)
    max_query_calls: int = Field(default=4096, ge=1, le=100000)
    warm_repeats: int = Field(default=0, ge=0, le=3)
    bootstrap_seed: int = Field(default=42, ge=0)
    bootstrap_samples: int = Field(default=2000, ge=100, le=10000)
    slices: dict[str, list[str]] = Field(default_factory=dict)
    question_groups: dict[str, str] = Field(default_factory=dict)
    criteria: Criteria = Field(default_factory=Criteria)
    pricing: Pricing | None = None

    @model_validator(mode="after")
    def validate_scopes(self):
        if "all" in self.slices or any(
            not name or any(not tag for tag in tags) for name, tags in self.slices.items()
        ):
            raise ValueError("Slice names/tags must be nonblank; 'all' is reserved")
        if any(not group for group in self.question_groups.values()):
            raise ValueError("Question group names must be nonblank")
        return self

    def expanded(self) -> list[Variant]:
        count = len(self.variants) + sum(
            prod(len(values) for values in grid.axes.values()) for grid in self.grids
        )
        if not 1 <= count <= self.max_configurations:
            raise ValueError(
                f"Suite requires 1 to {self.max_configurations} configurations after expansion"
            )
        variants = list(self.variants)
        for grid in self.grids:
            for index, values in enumerate(product(*grid.axes.values()), 1):
                variants.append(
                    Variant.model_validate(
                        {
                            **grid.variant.model_dump(),
                            "name": f"{grid.variant.name}-{index:02d}",
                            "options": {
                                **grid.variant.options,
                                **dict(zip(grid.axes, values, strict=True)),
                            },
                        }
                    )
                )
        names = [variant.name for variant in variants]
        if len(names) != len(set(names)):
            raise ValueError("Expanded suite names must be unique")
        if self.baseline and self.baseline not in names:
            raise ValueError("Suite baseline must name an expanded configuration")
        return variants


class FrozenJob(StrictModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_-]+$", max_length=64)
    config: StrategyConfig
    chunk_size: int = Field(ge=1)
    chunk_overlap: int = Field(ge=0)
    prefixes_file: str | None = None
    results_file: str | None = None
    usage_file: str | None = None


class FrozenSuite(StrictModel):
    schema_version: Literal[1] = 1
    input_name: str
    phase: Literal["dev", "heldout", "all"]
    spec: SuiteSpec
    jobs: list[FrozenJob]
    baseline: str
    snapshot_hash: str
    questions_hash: str
    references_hash: str | None
    all_references_hash: str | None
    files: dict[str, str]
    provider_state_hash: str
    query_call_upper_bound: int
    heldout_use: dict[str, Any] = Field(default_factory=dict)


class FrozenShortlist(StrictModel):
    schema_version: Literal[1] = 1
    selection_phase: Literal["dev"]
    configuration_hash: str
    jobs: list[FrozenJob] = Field(min_length=1, max_length=32)
    baseline: str
    spec: SuiteSpec
    corpus_hash: str
    references_hash: str
    provider_state_hash: str
