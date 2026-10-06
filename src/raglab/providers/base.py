"""Provider contracts kept separate from retrieval logic."""

from typing import Protocol

import numpy as np


class EmbeddingProvider(Protocol):
    model_name: str

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...
