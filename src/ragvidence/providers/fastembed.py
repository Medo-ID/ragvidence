"""Optional local FastEmbed adapter."""

import numpy as np


class FastEmbedProvider:
    def __init__(self, model_name: str) -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError("Semantic retrieval requires: uv sync --extra semantic") from exc
        self.model_name = model_name
        self.cache_identity = {
            "adapter": "fastembed-v1",
            "model": model_name,
            "document_encoding": "embed",
            "query_encoding": "query_embed",
        }
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray(list(self._model.embed(texts)), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(list(self._model.query_embed(text)), dtype=np.float32)[0]
