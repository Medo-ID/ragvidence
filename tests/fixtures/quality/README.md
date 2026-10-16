# Reviewed compatibility corpus

Eight fictional source records and twelve fixed questions (eleven answerable),
authored before the model check. Quotes are manually specified in `review.spec.json`;
the verification script resolves their unique occurrences to original source spans.
The legacy-version distractor, qualifiers, paraphrases, multiple spans/sources and
unanswerable case exercise more than a single successful query. Related reset
questions share a tag; this tiny fixture is not an independent production sample.

No model generates the references. Results may pass, fail or tie; the check records
them without tuning the fixtures or declaring a generally superior technique.
`dev`/`heldout` are preserved for testing separate denominators, not a claim that this
public repository fixture is an unseen evaluation set.
