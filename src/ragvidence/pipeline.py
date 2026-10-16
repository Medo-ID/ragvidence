"""Resolve a retrieval configuration and build its provider-backed stages."""

from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from ragvidence.budgets import tokenizer_hash
from ragvidence.config import Settings
from ragvidence.models import StrategyConfig
from ragvidence.providers import OllamaEmbeddingProvider, OpenAICompatibleEmbeddingProvider
from ragvidence.strategies import BM25Strategy, SemanticStrategy
from ragvidence.strategies.base import RetrievalStrategy
from ragvidence.strategies.hybrid import HybridStrategy
from ragvidence.strategies.parent_child import ParentChildStrategy


def resolve_config(config: StrategyConfig, settings: Settings) -> StrategyConfig:
    if config.strategy == "imported":
        raise ValueError("Use import-run for external retrieval results")
    extended = (
        config.strategy == "hybrid"
        or config.child_splitter != "none"
        or config.query_variants
        or config.reranker_model
        or config.context_budget
    )
    resolved = {
        **config.model_dump(),
        "candidate_k": config.candidate_k or (max(20, config.k) if extended else config.k),
    }
    if config.tokenizer_file:
        resolved["tokenizer_hash"] = tokenizer_hash(config.tokenizer_file)
    if config.strategy in {"semantic", "hybrid"}:
        resolved.update(
            model=config.model or settings.embedding_model,
            provider=config.provider or settings.embedding_provider,
        )
    return StrategyConfig.model_validate(resolved)


def semantic_strategy(
    config: StrategyConfig, cache_dir: Path, settings: Settings
) -> SemanticStrategy:
    model = config.model or settings.embedding_model
    provider_name = config.provider or settings.embedding_provider
    provider = None
    if provider_name == "ollama":
        provider = OllamaEmbeddingProvider(
            model, settings.embedding_base_url or "http://localhost:11434"
        )
    elif provider_name == "openai_compatible":
        if not settings.embedding_base_url:
            raise RuntimeError("RAGVIDENCE_EMBEDDING_BASE_URL is required")
        key = settings.embedding_api_key.get_secret_value() if settings.embedding_api_key else None
        provider = OpenAICompatibleEmbeddingProvider(model, settings.embedding_base_url, key)
    elif provider_name != "fastembed":
        raise RuntimeError(f"Unsupported embedding provider: {provider_name}")
    return SemanticStrategy(model, cache_dir=cache_dir / "embeddings", provider=provider)


def build_strategy(
    config: StrategyConfig, cache_dir: Path, settings: Settings
) -> RetrievalStrategy:
    if config.strategy == "bm25":
        strategy: RetrievalStrategy = BM25Strategy()
    elif config.strategy == "semantic":
        strategy = semantic_strategy(config, cache_dir, settings)
    elif config.strategy == "hybrid":
        strategy = HybridStrategy(
            BM25Strategy(),
            semantic_strategy(config, cache_dir, settings),
            candidate_k=config.branch_k or config.candidate_k or config.k,
            fixed_depth=config.branch_k is not None,
            lexical_weight=config.lexical_weight,
            constant=config.rrf_constant,
        )
    else:
        raise ValueError("Imported runs cannot be executed as native strategies")
    if config.child_splitter != "none":
        strategy = ParentChildStrategy(
            strategy,
            splitter=config.child_splitter,
            size=config.child_size,
            overlap=config.child_overlap,
            candidate_k=config.child_k or config.candidate_k or config.k,
            fixed_depth=config.child_k is not None,
        )
    return strategy


def vector_cache_state(strategy) -> str:
    """Describe only observed vector reuse; model/OS cache warmth is unknown."""
    if isinstance(strategy, SemanticStrategy):
        return "warm_vectors" if strategy.cache_hit else "cold_vectors"
    for attribute in ("semantic", "child_strategy"):
        child = getattr(strategy, attribute, None)
        if child is not None:
            return vector_cache_state(child)
    return "not_applicable"


@lru_cache(maxsize=1)
def runtime_versions() -> dict:
    versions = {}
    for name in ("bm25s", "numpy", "fastembed", "onnxruntime", "tokenizers"):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            continue
    return versions
