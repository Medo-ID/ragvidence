"""Materialize search inputs and explicit question-only/prefix sidecars."""

import json
from pathlib import Path

from pydantic import Field

from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import SourceUnit, StrategyConfig, StrictModel


def read_sidecar(path: Path):
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Sidecar input exceeds 10 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def load_variants(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    values = read_sidecar(path)
    if not isinstance(values, dict) or any(
        not isinstance(key, str)
        or not isinstance(items, list)
        or not items
        or len(items) > 8
        or any(not isinstance(item, str) or not item.strip() for item in items)
        for key, items in values.items()
    ):
        raise ValueError("Variants must map question IDs to one to eight nonblank query strings")
    return values


class ReviewedPrefix(StrictModel):
    text_hash: str
    prefix: str = Field(min_length=1)


def prepare_sources(
    snapshot: CorpusSnapshot,
    config: StrategyConfig,
    prefixes_file: Path | None,
) -> list[SourceUnit]:
    originals = {source.source_unit_id: source for source in snapshot.documents}
    prefixes = {}
    if prefixes_file:
        values = read_sidecar(prefixes_file)
        if not isinstance(values, dict) or set(values) != set(originals):
            raise ValueError("Prefixes must map every original source ID exactly once")
        for source_id, value in values.items():
            prefix = ReviewedPrefix.model_validate(value)
            if (
                prefix.text_hash != originals[source_id].metadata["text_hash"]
                or not prefix.prefix.strip()
            ):
                raise ValueError("Reviewed prefix text hash or nonblank text does not match source")
            prefixes[source_id] = prefix.prefix
    if config.representation == "contextual" and not prefixes:
        raise ValueError("contextual requires --prefixes FILE with reviewed source prefixes")
    if prefixes and config.representation != "contextual":
        raise ValueError("--prefixes requires contextual representation")
    selected = snapshot.documents if config.child_splitter != "none" else snapshot.passages
    if config.representation == "heading_context" and not any(
        source.heading_path for source in selected
    ):
        raise ValueError(
            "heading-context requires authentic source headings; "
            "choose body representation for flat text"
        )
    sources = []
    for source in selected:
        origin = source.metadata.get("origin_source_id", source.source_unit_id)
        metadata = {**source.metadata, **({"context_prefix": prefixes[origin]} if prefixes else {})}
        sources.append(source.model_copy(update={"metadata": metadata}))
    return sources
