"""Count rendered retrieval context and select whole ranked passages that fit."""

from importlib.metadata import version
from pathlib import Path

from ragvidence.artifacts import content_hash
from ragvidence.context import passages_for_hits, render_context
from ragvidence.models import RetrievalHit, SourceUnit


def tokenizer_hash(path: str) -> str:
    target = Path(path)
    if target.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Tokenizer file exceeds 50 MiB")
    return content_hash(target.read_text(encoding="utf-8"))


class ContextCounter:
    def __init__(self, tokenizer_file: str | None = None, expected_hash: str | None = None):
        self.tokenizer = None
        self.identity = {"adapter": "unicode-codepoints-v1", "unit": "characters", "exact": True}
        if tokenizer_file:
            path = Path(tokenizer_file)
            if path.stat().st_size > 50 * 1024 * 1024:
                raise ValueError("Tokenizer file exceeds 50 MiB")
            raw = path.read_text(encoding="utf-8")
            digest = content_hash(raw)
            if expected_hash and digest != expected_hash:
                raise ValueError("Tokenizer file changed after configuration resolution")
            try:
                from tokenizers import Tokenizer
            except ImportError as exc:
                raise RuntimeError(
                    "Local tokenizer counting requires 'ragvidence[semantic]'"
                ) from exc
            self.tokenizer = Tokenizer.from_str(raw)
            # Count the complete context, even if the saved inference tokenizer
            # was configured to truncate or pad model inputs.
            self.tokenizer.no_truncation()
            self.tokenizer.no_padding()
            self.identity = {
                "adapter": "huggingface-tokenizers-v1",
                "unit": "tokens",
                "exact": True,
                "file_hash": digest,
                "version": version("tokenizers"),
                "add_special_tokens": False,
                "truncation": False,
                "padding": False,
            }

    def count(self, text: str) -> int:
        return (
            len(self.tokenizer.encode(text, add_special_tokens=False).ids)
            if self.tokenizer
            else len(text)
        )


def select_context(
    hits: list[RetrievalHit],
    sources: dict[str, SourceUnit],
    *,
    k: int,
    budget: int | None,
    counter: ContextCounter,
) -> tuple[list[RetrievalHit], dict]:
    selected, skipped = [], []
    for hit in hits:
        if len(selected) == k:
            break
        proposed = [*selected, hit]
        rendered = render_context(passages_for_hits(proposed, sources))
        count = counter.count(rendered)
        if budget is not None and count > budget:
            skipped.append({"source_unit_id": hit.source_unit_id, "proposed_count": count})
        else:
            selected.append(hit.model_copy(update={"rank": len(selected) + 1}))
    rendered = render_context(passages_for_hits(selected, sources))
    return selected, {
        **counter.identity,
        "count": counter.count(rendered),
        "budget": budget,
        "scope": "rendered_retrieval_context",
        "skipped": skipped,
        "policy": "ranked-whole-passages-v1",
    }
