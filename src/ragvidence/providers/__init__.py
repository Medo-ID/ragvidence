"""Embedding provider adapters."""

from ragvidence.providers.base import EmbeddingProvider
from ragvidence.providers.fastembed import FastEmbedProvider
from ragvidence.providers.remote import OllamaEmbeddingProvider, OpenAICompatibleEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "FastEmbedProvider",
    "OllamaEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
]
