"""Portable settings resolution, without implicit project or dotenv discovery."""

import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Literal

from dotenv import dotenv_values
from pydantic import Field, model_validator

from ragvidence.models import CompressionConfig, FilterConfig, MMRConfig, RewriteConfig, StrictModel


class PortableOptions(StrictModel):
    output: Path = Path("ragvi-reports")
    cache_dir: Path | None = None
    formats: list[str] = Field(default_factory=lambda: ["html"])
    k: int = Field(default=2, ge=1)
    chunk_size: int = Field(default=500, ge=1)
    chunk_overlap: int = Field(default=50, ge=0)
    text_field: str | None = Field(default=None, min_length=1)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_files: int = Field(default=1000, ge=1)
    max_file_bytes: int = Field(default=20 * 1024 * 1024, ge=1)
    max_total_bytes: int = Field(default=100 * 1024 * 1024, ge=1)
    max_records: int = Field(default=10000, ge=1)
    max_extracted_characters: int = Field(default=20 * 1024 * 1024, ge=1)
    base_retriever: Literal["bm25", "semantic", "hybrid"] = "bm25"
    provider: Literal["fastembed", "ollama", "openai_compatible"] | None = None
    model: str | None = None
    representation: Literal["body", "heading_context", "contextual"] = "body"
    child_splitter: Literal["recursive", "markdown"] = "recursive"
    reranker_model: str | None = None
    branch_k: int | None = Field(default=None, ge=1)
    child_k: int | None = Field(default=None, ge=1)
    query_k: int | None = Field(default=None, ge=1)
    rerank_k: int | None = Field(default=None, ge=1)
    context_budget: int | None = Field(default=None, ge=1)
    tokenizer_file: Path | None = None
    lexical_weight: float = Field(default=0.5, gt=0, lt=1)
    rrf_constant: int = Field(default=60, ge=0)
    filters: FilterConfig | None = None
    mmr: MMRConfig | None = None
    rewrite: RewriteConfig | None = None
    compression: CompressionConfig | None = None

    @model_validator(mode="after")
    def validate_options(self) -> "PortableOptions":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk-overlap must be smaller than chunk-size")
        if not self.formats or any(
            value not in {"html", "json", "markdown"} for value in self.formats
        ):
            raise ValueError("Supported report formats: html, json, markdown")
        if any(not pattern for pattern in [*self.include_patterns, *self.exclude_patterns]):
            raise ValueError("Include/exclude patterns must not be empty")
        return self


def user_config_path() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "ragvidence/config.toml"


def _read_config(path: Path) -> dict[str, Any]:
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Configuration exceeds 1 MiB")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        values = json.loads(text)
    elif path.suffix.lower() == ".toml":
        values = tomllib.loads(text)
    else:
        raise ValueError("Configuration must use .toml or .json")
    if not isinstance(values, dict):
        raise ValueError("Configuration must be an object of portable options")
    unknown = set(values) - set(PortableOptions.model_fields)
    if unknown:
        raise ValueError(f"Unknown portable configuration fields: {', '.join(sorted(unknown))}")
    for key in ("output", "cache_dir", "tokenizer_file"):
        if values.get(key) is not None:
            if not isinstance(values[key], str):
                raise ValueError(f"Configuration {key} must be a path string")
            resolved = Path(values[key]).expanduser()
            values[key] = resolved if resolved.is_absolute() else path.resolve().parent / resolved
    return values


def resolve_portable_options(
    overrides: dict[str, Any],
    *,
    config_file: Path | None = None,
    env_file: Path | None = None,
) -> PortableOptions:
    values: dict[str, Any] = {}
    user_file = user_config_path()
    if user_file.is_file():
        values.update(_read_config(user_file))
    if config_file is not None:
        values.update(_read_config(config_file))
    environment: dict[str, Any] = {}
    if env_file is not None:
        if not env_file.is_file():
            raise ValueError(f"Environment file does not exist: {env_file}")
        if env_file.stat().st_size > 1024 * 1024:
            raise ValueError("Environment file exceeds 1 MiB")
        # No interpolation of unrelated ambient secrets into paths/options.
        environment.update(dotenv_values(env_file, interpolate=False))
    environment.update(os.environ)
    for field in PortableOptions.model_fields:
        raw = environment.get("RAGVIDENCE_" + field.upper())
        if raw is not None:
            if field in {
                "formats",
                "include_patterns",
                "exclude_patterns",
                "filters",
                "mmr",
                "rewrite",
                "compression",
            }:
                try:
                    raw = json.loads(raw)
                except ValueError as exc:
                    kind = (
                        "a JSON array"
                        if field in {"formats", "include_patterns", "exclude_patterns"}
                        else "a JSON object"
                    )
                    raise ValueError(f"RAGVIDENCE_{field.upper()} must be {kind}") from exc
            values[field] = raw
    values.update({key: value for key, value in overrides.items() if value is not None})
    for key in ("output", "cache_dir", "tokenizer_file"):
        if values.get(key) is not None:
            values[key] = Path(values[key]).expanduser()
    return PortableOptions.model_validate(values)
