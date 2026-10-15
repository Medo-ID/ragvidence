"""Optional answer inspection using only retrieved source context."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from ragvidence.config import Settings
from ragvidence.context import passages_for_hits, render_context
from ragvidence.data import load_dataset
from ragvidence.models import ExperimentRun
from ragvidence.providers.remote import ChatProvider
from ragvidence.validation import validate_run

SYSTEM_PROMPT = (
    "Answer only from the provided retrieved context. Cite source IDs in square brackets. "
    "If the context is insufficient, say so explicitly."
)


def generate_answers(workspace: Path, run: ExperimentRun, settings: Settings) -> dict[str, Any]:
    sources, questions = load_dataset(workspace)
    validate_run(run, sources, questions)
    if settings.generation_provider not in {"ollama", "openai_compatible"}:
        raise RuntimeError("RAGVIDENCE_GENERATION_PROVIDER must be ollama or openai_compatible")
    if not settings.generation_model or not settings.generation_base_url:
        raise RuntimeError("Generation model and base URL are required")
    key = settings.generation_api_key.get_secret_value() if settings.generation_api_key else None
    provider = ChatProvider(
        settings.generation_provider, settings.generation_model, settings.generation_base_url, key
    )
    source_by_id = {item.source_unit_id: item for item in sources}
    question_by_id = {item.question_id: item for item in questions}
    answers = []
    for query in run.queries:
        context = (
            query.rendered_context
            if query.rendered_context is not None
            else render_context(passages_for_hits(query.hits, source_by_id))
        )
        user = f"Question: {question_by_id[query.question_id].question}\n\nContext:\n" + context
        started = time.perf_counter()
        answer = provider.answer(SYSTEM_PROMPT, user)
        answers.append(
            {
                "question_id": query.question_id,
                "answer": answer,
                "source_unit_ids": [hit.source_unit_id for hit in query.hits],
                "latency_ms": (time.perf_counter() - started) * 1000,
            }
        )
    return {
        "run_id": run.manifest.run_id,
        "provider": settings.generation_provider,
        "model": settings.generation_model,
        "answers": answers,
        "warning": "Generated answers are for inspection and are not retrieval-evaluation labels.",
    }
