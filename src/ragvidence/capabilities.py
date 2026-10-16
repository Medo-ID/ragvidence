"""One catalog defines portable technique presets and their prerequisites."""

from dataclasses import asdict, dataclass

from ragvidence.models import StrategyConfig


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    requirements: str


CAPABILITIES = [
    Capability("bm25", "Lexical ranking over independent passages", "None"),
    Capability(
        "semantic", "Dense cosine ranking", "Embedding provider; semantic extra for local models"
    ),
    Capability("hybrid", "Weighted BM25/dense reciprocal rank fusion", "Embedding provider"),
    Capability(
        "rerank", "Cross-encoder over retrieved candidates", "semantic extra and --reranker-model"
    ),
    Capability("parent-child", "Search children and return full originals", "None for BM25 base"),
    Capability(
        "heading-context", "Index authentic heading paths with body text", "Headings in the source"
    ),
    Capability("contextual", "Index reviewed source prefixes with body text", "--prefixes FILE"),
    Capability("multi-query", "Fuse original query and supplied variants", "--variants FILE"),
    Capability("import-data", "Inspect external ID or exact-span results", "--results FILE"),
]


def catalog() -> list[dict]:
    return [asdict(capability) for capability in CAPABILITIES]


def preset(name: str, options, *, variants: dict[str, list[str]]) -> StrategyConfig:
    values = options.model_dump(
        include={
            "k",
            "model",
            "provider",
            "representation",
            "branch_k",
            "child_k",
            "query_k",
            "rerank_k",
            "context_budget",
            "reranker_model",
            "lexical_weight",
            "rrf_constant",
        }
    )
    values.update(
        name=name,
        strategy=name if name in {"bm25", "semantic", "hybrid"} else options.base_retriever,
        query_variants=variants,
    )
    if options.tokenizer_file:
        values["tokenizer_file"] = str(options.tokenizer_file)
    if name == "parent-child":
        values.update(
            child_splitter=options.child_splitter,
            child_size=options.chunk_size,
            child_overlap=options.chunk_overlap,
        )
    if name in {"contextual", "heading-context"}:
        values["representation"] = "contextual" if name == "contextual" else "heading_context"
    if name == "rerank" and not options.reranker_model:
        raise ValueError("rerank requires --reranker-model MODEL")
    if name == "multi-query" and not variants:
        raise ValueError("multi-query requires --variants FILE with question-ID mappings")
    if name == "import-data":
        if (
            variants
            or options.reranker_model
            or options.representation != "body"
            or any(
                value is not None
                for value in (options.branch_k, options.child_k, options.query_k, options.rerank_k)
            )
        ):
            raise ValueError(
                "import-data accepts returned results and context budgets, not retrieval modifiers"
            )
        values["strategy"] = "imported"
        values["model"] = values["provider"] = None
    return StrategyConfig.model_validate(values)
