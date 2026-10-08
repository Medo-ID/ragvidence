import numpy as np
import pytest

from raglab.providers import remote
from raglab.providers.remote import (
    ChatProvider,
    OllamaEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
)


def test_remote_provider_rejects_non_http_url() -> None:
    provider = OpenAICompatibleEmbeddingProvider("model", "file:///tmp/provider")

    with pytest.raises(RuntimeError, match="must use http or https"):
        provider.embed_query("query")


def test_remote_provider_rejects_embedded_credentials() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        "model", "https://user:password@example.test/v1"
    )

    with pytest.raises(RuntimeError, match="must not contain embedded credentials"):
        provider.embed_query("query")


def test_openai_compatible_embedding_order(monkeypatch) -> None:
    monkeypatch.setattr(
        remote,
        "_post_json",
        lambda *args, **kwargs: {
            "data": [{"index": 1, "embedding": [0, 1]}, {"index": 0, "embedding": [1, 0]}]
        },
    )
    provider = OpenAICompatibleEmbeddingProvider("model", "https://example.test/v1", "secret")
    assert np.array_equal(provider.embed_documents(["a", "b"]), [[1, 0], [0, 1]])


def test_ollama_embedding_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        remote, "_post_json", lambda *args, **kwargs: {"embeddings": [[1, 2], [3, 4]]}
    )
    assert OllamaEmbeddingProvider("model").embed_documents(["a", "b"]).shape == (2, 2)


def test_chat_adapter_extracts_content(monkeypatch) -> None:
    monkeypatch.setattr(
        remote,
        "_post_json",
        lambda *args, **kwargs: {"choices": [{"message": {"content": "answer"}}]},
    )
    provider = ChatProvider("openai_compatible", "model", "https://example.test/v1")
    assert provider.answer("system", "user") == "answer"
