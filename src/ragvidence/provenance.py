"""Independent identities for original data, search inputs and reviewed labels."""

from ragvidence.artifacts import content_hash
from ragvidence.models import (
    InputPreparation,
    QuestionCase,
    SearchQuestion,
    SourceUnit,
    StrategyConfig,
)
from ragvidence.representation import build_records


def corpus_identity(sources: list[SourceUnit]) -> str:
    return content_hash(
        [
            {
                "source_unit_id": source.source_unit_id,
                "document_id": source.document_id,
                "body": source.body,
                "heading_path": source.heading_path,
                "metadata": {
                    key: value for key, value in source.metadata.items() if key != "context_prefix"
                },
            }
            for source in sources
        ]
    )


def configuration_identity(config: StrategyConfig, preparation: InputPreparation | None) -> str:
    return content_hash(
        config
        if preparation is None
        else {
            "retrieval": config,
            "input_preparation": preparation,
        }
    )


def question_identity(questions: list[SearchQuestion]) -> str:
    return content_hash(
        [
            {"question_id": question.question_id, "question": question.question}
            for question in questions
        ]
    )


def reference_identity(sources: list[SourceUnit], questions: list[QuestionCase]) -> str:
    return content_hash(
        {
            "sources": [
                {"source_unit_id": source.source_unit_id, "evidence_ids": source.evidence_ids}
                for source in sources
            ],
            "questions": questions,
        }
    )


def representation_identity(sources: list[SourceUnit], config: StrategyConfig) -> str:
    return content_hash(
        {
            "implementation": "representations-v1",
            "representation": config.representation,
            "child_splitter": config.child_splitter,
            "child_size": config.child_size,
            "child_overlap": config.child_overlap,
            "records": [
                {
                    "source_unit_id": record.source.source_unit_id,
                    "searchable_text": record.searchable_text,
                }
                for record in build_records(sources, config.representation)
            ],
        }
    )
