"""Ordinary-file ingestion with immutable original text and passage provenance."""

from ragvidence.ingestion.loaders import load_corpus
from ragvidence.ingestion.models import CorpusSnapshot

__all__ = ["CorpusSnapshot", "load_corpus"]
