# Privacy and providers

The core BM25 workflow is fully local and uses no account, analytics or API key. The optional FastEmbed path downloads a model once and then performs inference locally.

`.env`, workspaces, caches and generated reports are git-ignored. Reports should contain source/evidence identifiers and short previews, not complete private documents. Never place credentials in a source JSONL file, report or command argument.

The optional Ollama and OpenAI-compatible adapters use endpoints and credentials supplied by the user. Before a remote embedding or generation run, the CLI discloses that source text and questions will be transmitted. Credentials are loaded from `.env`, represented as secret values and never written to manifests or reports.

Provider URLs are restricted to `http` and `https` and may not contain embedded credentials. Use plain HTTP only for a trusted local service such as Ollama; use HTTPS for remote providers.

For semantic retrieval, choose `--provider ollama` or `--provider openai_compatible` and configure the corresponding `RAGVIDENCE_EMBEDDING_*` values. For optional answer inspection, configure `RAGVIDENCE_GENERATION_*` and run `ragvi generate`. Generated answers are kept separate from retrieval labels and never change evaluation scores.

Before sharing a report, inspect it for confidential source names, metadata and previews. “Local by default” does not make an exported report safe automatically.
