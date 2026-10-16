"""Resolve stage flags over nested portable configuration without CLI behavior."""

from pathlib import Path

from ragvidence.models import FilterConfig
from ragvidence.portable_config import PortableOptions


def load_filters(path: Path) -> FilterConfig:
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Filter configuration exceeds 1 MiB")
    return FilterConfig.model_validate_json(path.read_text(encoding="utf-8"))


def apply_stage_flags(options: PortableOptions, technique: str, flags: dict) -> PortableOptions:
    values = options.model_dump()
    if flags.get("filters"):
        values["filters"] = load_filters(flags["filters"]).model_dump()
    mappings = {
        "mmr": {"mmr_lambda": "lambda_mult", "mmr_candidates": "candidates"},
        "rewrite": {
            "rewrite_model": "model",
            "rewrite_provider": "provider",
            "rewrite_count": "count",
            "rewrite_original": "include_original",
            "rewrite_failure": "failure",
        },
        "compression": {
            "compressor": "mode",
            "compression_max_spans": "max_spans",
            "compression_model": "model",
            "compression_provider": "provider",
            "compression_failure": "failure",
        },
    }
    for stage, mapping in mappings.items():
        overrides = {
            target: flags[key] for key, target in mapping.items() if flags.get(key) is not None
        }
        if overrides:
            values[stage] = {**(values[stage] or {}), **overrides}
            if stage == "rewrite" and "count" not in values[stage] and technique == "rewrite":
                values[stage]["count"] = 1
            if stage == "compression" and "model" in overrides and "mode" not in overrides:
                values[stage]["mode"] = "model"
    # Keep parsed contents in configuration identities; no runtime file dependency.
    return PortableOptions.model_validate(values)
