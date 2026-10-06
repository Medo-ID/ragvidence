"""Embedding provider adapters."""

from raglab.providers.base import EmbeddingProvider
from raglab.providers.fastembed import FastEmbedProvider
from raglab.providers.remote import OllamaEmbeddingProvider, OpenAICompatibleEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "FastEmbedProvider",
    "OllamaEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
]
