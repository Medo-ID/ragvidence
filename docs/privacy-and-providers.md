# Privacy and providers

The core BM25 workflow is fully local and uses no account, analytics or API key. The optional FastEmbed path downloads a model once and then performs inference locally.

`.env`, workspaces, caches and generated reports are git-ignored. Reports can contain full returned passages, questions, metadata, transformation prompts and model outputs. Internal artifacts can contain the original corpus and reviewed references. Never place credentials in a source JSONL file, report or command argument.

The optional Ollama and OpenAI-compatible adapters use endpoints and credentials supplied by the user. Before a remote embedding or generation run, the CLI discloses that source text and questions will be transmitted. Credentials are loaded from `.env`, represented as secret values and never written to manifests or reports.

Provider URLs are restricted to `http` and `https` and may not contain embedded credentials. Use plain HTTP only for a trusted local service such as Ollama; use HTTPS for remote providers.

For semantic retrieval, choose `--provider ollama` or `--provider openai_compatible` and configure the corresponding `RAGVIDENCE_EMBEDDING_*` values. For optional answer inspection, configure `RAGVIDENCE_GENERATION_*` and run `ragvi generate`. Generated answers are kept separate from retrieval labels and never change evaluation scores.

Before sharing a report, inspect it for confidential source text, names, questions, metadata and prompts. “Local by default” does not make an exported report safe automatically.

The portable BM25 path ignores `.env` in the input/current directory unless explicitly
selected with `--env-file`. It never sends
data to a provider, and leaves original files unchanged. Portable report exports
contain full returned passages. Its internal `snapshot.json` contains original
loaded text; keep internal artifacts separate from the selected shareable report.
New workspace evaluations also retain a private source/run snapshot for integrity
validation; report exports omit that internal validation snapshot.

Portable comparisons freeze original inputs, references and selected sidecars in a
private comparison directory. Completed jobs are validated before resume; no original
input is reread on resume. Share selected exports, not the entire comparison directory,
when original corpus text or reviewed labels should remain private. Comparison exports
include retrieved passages and source locations. Supplied token usage/pricing produces
labeled estimates; the tool does not fetch billing or pricing from external accounts.

M6 query transformations use separate `RAGVIDENCE_TRANSFORM_BASE_URL` and
`RAGVIDENCE_TRANSFORM_API_KEY` settings. The CLI discloses the transfer before
execution. Rewriting sends only the question and variant limit. Optional model
compression sends the question and candidate bodies. Neither receives reviewed
evidence IDs/reference answers from evaluation. Deterministic sentence compression
does not call a provider. MMR uses the configured embedding adapter and only indexes
the union of source units permitted by the run's metadata scopes.

Transformation prompts, bounded raw outputs and selected spans are retained in run
stage evidence; failed default-fail attempts retain private `failure.json` traces.
Model compression prompts may therefore expose full candidate text in reports.
Credentials never enter these artifacts, and endpoint identities are hashes.
Share only exports whose source text, questions and prompts you have reviewed.
