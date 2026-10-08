"""Minimal user-owned HTTP provider adapters without framework lock-in."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import numpy as np

MAX_RESPONSE_BYTES = 25 * 1024 * 1024


def _validate_http_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise RuntimeError("Provider URL must use http or https and include a host")
    if parsed.username is not None or parsed.password is not None:
        raise RuntimeError("Provider URL must not contain embedded credentials")


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: float = 60.0) -> dict:
    _validate_http_url(url)
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310: URL validated above
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError("Provider response exceeds the 25 MiB safety limit")
            value = json.loads(raw.decode())
    except HTTPError as exc:
        raise RuntimeError(f"Provider request failed with HTTP {exc.code}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Provider request failed: {type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Provider returned an invalid JSON response")
    return value


class OpenAICompatibleEmbeddingProvider:
    def __init__(self, model_name: str, base_url: str, api_key: str | None = None) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]

    def _embed(self, texts: list[str]) -> np.ndarray:
        value = _post_json(
            f"{self.base_url}/embeddings", {"model": self.model_name, "input": texts}, self._headers
        )
        try:
            ordered = sorted(value["data"], key=lambda item: item["index"])
            return np.asarray([item["embedding"] for item in ordered], dtype=np.float32)
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Provider response is missing valid embedding data") from exc


class OllamaEmbeddingProvider:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434") -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        value = _post_json(
            f"{self.base_url}/api/embed", {"model": self.model_name, "input": texts}, {}
        )
        try:
            return np.asarray(value["embeddings"], dtype=np.float32)
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Ollama response is missing valid embeddings") from exc

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_documents([text])[0]


class ChatProvider:
    def __init__(
        self, provider: str, model: str, base_url: str, api_key: str | None = None
    ) -> None:
        self.provider, self.model, self.base_url = provider, model, base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def answer(self, system: str, user: str) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        if self.provider == "ollama":
            value = _post_json(
                f"{self.base_url}/api/chat",
                {"model": self.model, "messages": messages, "stream": False},
                {},
            )
            try:
                return str(value["message"]["content"])
            except (KeyError, TypeError) as exc:
                raise RuntimeError("Ollama response is missing message content") from exc
        value = _post_json(
            f"{self.base_url}/chat/completions",
            {"model": self.model, "messages": messages, "temperature": 0},
            self._headers,
        )
        try:
            return str(value["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Provider response is missing message content") from exc
