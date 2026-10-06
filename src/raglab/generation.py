"""Optional answer inspection using only retrieved source context."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from raglab.config import Settings
from raglab.data import load_dataset
from raglab.models import ExperimentRun
from raglab.providers.remote import ChatProvider

SYSTEM_PROMPT = (
    "Answer only from the provided retrieved context. Cite source IDs in square brackets. "
    "If the context is insufficient, say so explicitly."
)


def generate_answers(workspace: Path, run: ExperimentRun, settings: Settings) -> dict[str, Any]:
    if settings.generation_provider not in {"ollama", "openai_compatible"}:
        raise RuntimeError("RAGLAB_GENERATION_PROVIDER must be ollama or openai_compatible")
    if not settings.generation_model or not settings.generation_base_url:
        raise RuntimeError("Generation model and base URL are required")
    key = settings.generation_api_key.get_secret_value() if settings.generation_api_key else None
    provider = ChatProvider(
        settings.generation_provider, settings.generation_model, settings.generation_base_url, key
    )
    sources, questions = load_dataset(workspace)
    source_by_id = {item.source_unit_id: item for item in sources}
    question_by_id = {item.question_id: item for item in questions}
    answers = []
    for query in run.queries:
        context = []
        for hit in query.hits:
            source = source_by_id[hit.source_unit_id]
            context.append(
                f"[{source.source_unit_id}] {' > '.join(source.heading_path)}\n{source.body}"
            )
        user = (
            f"Question: {question_by_id[query.question_id].question}\n\nContext:\n"
            + "\n\n".join(context)
        )
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
