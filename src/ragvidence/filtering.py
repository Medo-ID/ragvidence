"""Typed metadata predicates, applied to sources before any ranking/expansion."""

from ragvidence.models import FilterConfig, MetadataPredicate, SourceUnit

_MISSING = object()


def metadata_value(metadata: dict, path: str):
    value = metadata
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return _MISSING
        value = value[key]
    return value


def _same_kind(left, right) -> bool:
    numeric = {int, float}
    return type(left) is type(right) or (type(left) in numeric and type(right) in numeric)


def matches(metadata: dict, predicate: MetadataPredicate) -> bool:
    value = metadata_value(metadata, predicate.field)
    if value is _MISSING or type(value) not in {str, bool, int, float, type(None)}:
        return False
    expected = predicate.value
    if predicate.op == "in":
        return any(_same_kind(value, item) and value == item for item in expected)
    if not _same_kind(value, expected):
        return False
    if predicate.op == "eq":
        return value == expected
    if type(value) not in {int, float, str}:
        return False
    return {
        "gt": lambda: value > expected,
        "gte": lambda: value >= expected,
        "lt": lambda: value < expected,
        "lte": lambda: value <= expected,
    }[predicate.op]()


def predicates_for(config: FilterConfig | None, question_id: str) -> list[MetadataPredicate]:
    return [*config.all, *config.questions.get(question_id, [])] if config else []


def eligible_sources(
    sources: list[SourceUnit], predicates: list[MetadataPredicate]
) -> list[SourceUnit]:
    return [source for source in sources if all(matches(source.metadata, p) for p in predicates)]
