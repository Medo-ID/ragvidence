"""Reproducible experiment execution."""

from __future__ import annotations

import hashlib
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from raglab import __version__
from raglab.data import canonical_dataset_bytes, load_dataset
from raglab.models import ExperimentRun, QueryRun, RunManifest, StrategyConfig
from raglab.providers import OllamaEmbeddingProvider, OpenAICompatibleEmbeddingProvider
from raglab.representation import build_records
from raglab.strategies import BM25Strategy, SemanticStrategy


def run_experiment(dataset: Path, config: StrategyConfig) -> ExperimentRun:
    sources, questions = load_dataset(dataset)
    records = build_records(sources, config.representation)
    strategy = BM25Strategy() if config.strategy == "bm25" else _semantic_strategy(dataset, config)
    started = time.perf_counter()
    strategy.index(records)
    index_ms = (time.perf_counter() - started) * 1000
    query_runs = []
    for question in questions:
        query_started = time.perf_counter()
        hits = strategy.search(question.question, k=config.k)
        query_runs.append(
            QueryRun(
                question_id=question.question_id,
                hits=hits,
                query_time_ms=(time.perf_counter() - query_started) * 1000,
            )
        )
    dataset_hash = hashlib.sha256(canonical_dataset_bytes(sources, questions)).hexdigest()
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    run_key = f"{config.name}:{dataset_hash}:{timestamp}".encode()
    return ExperimentRun(
        manifest=RunManifest(
            run_id=hashlib.sha256(run_key).hexdigest()[:12],
            created_at=timestamp,
            product_version=__version__,
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            dataset_hash=dataset_hash,
            config=config,
            index_time_ms=index_ms,
        ),
        queries=query_runs,
    )


def write_run(run: ExperimentRun, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing run: {output}")
    output.write_text(run.model_dump_json(indent=2), encoding="utf-8")


def _semantic_strategy(dataset: Path, config: StrategyConfig) -> SemanticStrategy:
    from raglab.config import Settings

    settings = Settings()
    provider_name = config.provider or settings.embedding_provider
    model = config.model or settings.embedding_model
    provider = None
    if provider_name == "ollama":
        provider = OllamaEmbeddingProvider(
            model, settings.embedding_base_url or "http://localhost:11434"
        )
    elif provider_name == "openai_compatible":
        if not settings.embedding_base_url:
            raise RuntimeError("RAGLAB_EMBEDDING_BASE_URL is required")
        key = settings.embedding_api_key.get_secret_value() if settings.embedding_api_key else None
        provider = OpenAICompatibleEmbeddingProvider(model, settings.embedding_base_url, key)
    elif provider_name != "fastembed":
        raise RuntimeError(f"Unsupported embedding provider: {provider_name}")
    return SemanticStrategy(
        model, cache_dir=dataset / ".raglab-cache" / "embeddings", provider=provider
    )
