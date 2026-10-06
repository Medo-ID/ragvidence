# Owner contribution 1 — evidence-level retrieval metrics

## Goal

Implement the pure functions in `src/raglab/evaluation/metrics.py` so the evaluator can decide whether retrieved results contain the evidence required by a question.

This module must not know how retrieval works. BM25, semantic retrieval, imported results, and future paid strategies will all pass the same ranked evidence structure into these functions.

## Input model

`retrieved_evidence` is ordered by retrieval rank. Each item is the set of evidence IDs contained by one retrieved source unit.

```python
ranking = [
    {"E-ORION-42-RESET"},  # rank 1
    {"E-ORION-41-RESET"},  # rank 2
]
```

Only the first `k` items are evaluated. If fewer than `k` hits exist, missing ranks count as non-relevant for precision.

## Required behavior

### `sufficient_evidence_at_k`

- Union the unique evidence IDs in the first `k` hits.
- Return `True` when every required ID is present.
- Return `False` when one or more required IDs are missing.
- Return `None` when `required_evidence` is empty because retrieval success is undefined for an unanswerable question.

### `evidence_coverage_at_k`

```text
unique required evidence found / unique required evidence
```

- Return a float from `0.0` to `1.0`.
- Count duplicate evidence only once.
- Return `None` for empty required evidence.

### `first_relevant_rank`

- A hit is relevant when its evidence set intersects required evidence.
- Return the first one-based rank within `k`.
- Return `None` when no relevant hit exists or required evidence is empty.

### `reciprocal_rank`

- Return `1 / first_relevant_rank`.
- Return `0.0` when required evidence exists but no relevant hit appears within `k`.
- Return `None` when required evidence is empty.

### `precision_at_k`

```text
number of relevant hits in the first k ranks / k
```

- A relevant hit contains at least one required evidence ID.
- Use `k` as the denominator even when fewer than `k` hits were returned.
- Return `None` when required evidence is empty.

### `classify_change`

Map the two booleans exactly:

| Baseline | Intervention | Result |
| --- | --- | --- |
| `False` | `True` | `fail_to_pass` |
| `True` | `False` | `pass_to_fail` |
| `True` | `True` | `pass_to_pass` |
| `False` | `False` | `fail_to_fail` |

## Shared validation rule

Every metric receiving `k` must raise:

```python
ValueError("k must be positive")
```

when `k <= 0`. Validate `k` before returning `None` for an unanswerable question so invalid configuration is never hidden.

## Constraints

- Pure functions only.
- Python 3.12 type hints.
- No Pydantic, NumPy, retrieval libraries, I/O, logging, or prints.
- Do not modify public names or signatures.
- Small private helpers are welcome when they remove duplication.
- Add docstrings where behavior is not obvious.
- Do not change tests merely to make an incorrect implementation pass.

## Run the acceptance tests

```bash
uv sync --dev
uv run pytest tests/unit/test_metrics.py
uv run ruff check src/raglab/evaluation/metrics.py tests/unit/test_metrics.py
```

When complete, provide the modified `metrics.py` file or a patch. The full project suite, type/contract review, edge-case review, and integration tests will be run before acceptance.

## Second contribution

The self-contained HTML report template is reserved for the owner after the authoritative result JSON schema is stable. A separate contract and fixture will be provided then.
