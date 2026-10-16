# Bring your own data

For ordinary files or folders, start with the 0.2.0
[portable commands](portable-file-usage.md). They need no manually prepared
workspace and support inspection or [reviewed span scoring](portable-techniques.md).
The schemas below are for reviewed
workspace evaluation, which requires expected evidence.

Start with a small reviewed slice—roughly 10–50 source units and 10–30 questions. The value comes from trustworthy labels, not corpus size.

## `sources.jsonl`

One JSON object per retrievable unit:

```json
{"source_unit_id":"S-17","document_id":"manual-a","heading_path":["Device A","Reset"],"body":"Hold the button for eight seconds.","evidence_ids":["E-RESET-17"],"metadata":{"language":"en"}}
```

- `source_unit_id`: stable unique identifier for the retrievable unit.
- `document_id`: stable source-document identifier.
- `heading_path`: authentic source headings; never generated gold-answer text.
- `body`: original text used in the body-only baseline.
- `evidence_ids`: reviewed facts/passages represented by this unit.
- `metadata`: optional information; not generally indexed. The development
  `contextual` representation explicitly indexes a reviewed `context_prefix`.

## `questions.jsonl`

```json
{"question_id":"Q-001","question":"How long is the reset?","split":"dev","answerable":true,"required_evidence_ids":["E-RESET-17"],"reference_answer":"Eight seconds.","tags":["procedure"]}
```

- Answerable questions require at least one evidence ID.
- Unanswerable questions must use an empty evidence-ID list.
- Use `dev` for diagnosis and intervention design.
- Keep `heldout` questions untouched until the intervention is frozen.
- A multi-evidence answer lists every required evidence ID.

## Avoid label leakage

Do not place reference answers, required-evidence IDs, grader notes or invented contextual hints into searchable text. Heading context must come from the source itself. If the intervention changes source boundaries, labels or `k`, it is no longer the controlled comparison used by the guided exercise.

## Validation

```bash
uv run ragvi validate workspaces/my-experiment
```

Validation rejects malformed JSON, unknown fields, duplicate IDs, answerability contradictions and required evidence that does not exist in the sources.

## Choosing `k`

Use the depth your application would actually pass downstream. A large `k` can hide retrieval failures while increasing noise and context cost. Keep `k` frozen across a baseline/intervention comparison.
