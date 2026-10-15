"""Shared numeric validation for provider and cache boundaries."""

from typing import Any

import numpy as np


def _numeric_array(value: Any) -> np.ndarray:
    try:
        raw = np.asarray(value)
        if raw.dtype.kind not in "iuf":
            raise ValueError("Expected real numeric vectors")
        return np.asarray(raw, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Embedding provider returned invalid numeric vectors") from exc


def document_vectors(value: Any, rows: int) -> np.ndarray:
    vectors = _numeric_array(value)
    if vectors.ndim != 2 or vectors.shape[0] != rows or vectors.shape[1] == 0:
        raise RuntimeError("Embedding provider returned an invalid document matrix")
    if not np.isfinite(vectors).all() or np.any(
        np.linalg.norm(vectors.astype(np.float64), axis=1) == 0
    ):
        raise RuntimeError("Embedding vectors must be finite and nonzero")
    return vectors


def query_vector(value: Any, dimensions: int) -> np.ndarray:
    vector = _numeric_array(value)
    if vector.ndim != 1 or vector.shape[0] != dimensions:
        raise RuntimeError("Embedding provider returned an invalid query vector")
    if not np.isfinite(vector).all() or np.linalg.norm(vector.astype(np.float64)) == 0:
        raise RuntimeError("Query embedding must be finite and nonzero")
    return vector
