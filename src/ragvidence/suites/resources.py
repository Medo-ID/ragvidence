"""Measured retrieval resources and explicitly supplied usage/pricing estimates."""

from pathlib import Path

from pydantic import Field

from ragvidence.models import StrictModel
from ragvidence.suites.models import Pricing
from ragvidence.suites.storage import read_json


class Usage(StrictModel):
    question_id: str
    model_id: str
    input_tokens: int = Field(ge=0, strict=True)
    output_tokens: int = Field(default=0, ge=0, strict=True)


def measured(values: list[float | int | None]) -> dict:
    known = [value for value in values if value is not None]
    return {
        "mean_known": sum(known) / len(known) if known else None,
        "known_count": len(known),
        "missing_count": len(values) - len(known),
    }


def resources(report: dict) -> dict:
    questions = report["questions"]
    states = {
        stage["details"].get("index_cache", "unknown")
        for q in questions
        for stage in q["stages"]
        if stage["name"] == "retrieval"
    }
    return {
        "query_ms": measured([q["query_time_ms"] for q in questions]),
        "runtime_versions": next(
            (
                stage["details"].get("runtime_versions", {})
                for q in questions
                for stage in q["stages"]
                if stage["name"] == "retrieval"
            ),
            {},
        ),
        "context_units": measured([q["context_measurement"].get("count") for q in questions]),
        "context_characters": measured([q["context_characters"] for q in questions]),
        "context_unit": next((q["context_measurement"]["unit"] for q in questions), None),
        "index_ms": report["manifest"]["index_time_ms"],
        "vector_cache": next(iter(states)) if len(states) == 1 else "unavailable",
        "model_cache": "unknown",
    }


def supplied_cost(
    path: Path | None,
    pricing: Pricing | None,
    question_ids: set[str],
    known_ids: set[str] | None = None,
) -> dict:
    result = {
        "source": "user_supplied_usage",
        "scope": "supplied_totals_not_inferred_from_repeats",
        "estimate": True,
        "cost": None,
        "currency": pricing.currency if pricing else None,
        "pricing_identity": pricing.identity if pricing else None,
        "input_tokens": None,
        "output_tokens": None,
    }
    if path is None:
        return result
    rows = [Usage.model_validate(value) for value in read_json(path)]
    identities = [(row.question_id, row.model_id) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("Usage entries must be unique per question/model")
    if {row.question_id for row in rows} - (known_ids or question_ids):
        raise ValueError("Usage contains unknown question IDs")
    rows = [row for row in rows if row.question_id in question_ids]
    result.update(
        input_tokens=sum(row.input_tokens for row in rows),
        output_tokens=sum(row.output_tokens for row in rows),
    )
    if (
        pricing
        and rows
        and {row.model_id for row in rows} <= pricing.rates.keys()
        and {row.question_id for row in rows} == question_ids
    ):
        result["cost"] = sum(
            (
                row.input_tokens * pricing.rates[row.model_id].input_per_million
                + row.output_tokens * pricing.rates[row.model_id].output_per_million
            )
            / 1e6
            for row in rows
        )
    result["covered_questions"] = len({row.question_id for row in rows})
    return result
