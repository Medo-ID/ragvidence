# RAG technique coverage

Source: [Production RAG with LangChain & Vector Databases](https://www.medo-id.com/book/prod-rag-langchain), read on 2026-10-15.

This describes the development source build. It does not claim that these additions
are available in the published 0.1.0 wheel. The implementation uses RAGvidence's
existing retrieval interfaces, without adding a LangChain dependency.

The product workflow is to diagnose a user's current RAG technique on their own
data, run built-in alternatives, and provide comparative evidence for their project
decision. Built-in techniques save users from implementing every retriever and
evaluation experiment themselves. Imported retrieval results provide a baseline
from an existing RAG system. Coverage below describes runnable experiments, rather
than a promise that an alternative will improve that system.

## Coverage from the resource

Portable entry points now share ordinary-file ingestion and original-span evidence
scoring. Run `ragvi techniques` or see [Portable techniques](portable-techniques.md).
`--reviewed` supplies validated references; unreviewed runs remain inspections.
The T11 model check covers two fingerprinted embedding configurations on one fixed
reviewed corpus. Broader quality/OS coverage remains release work; command availability
alone is not a claim of universal quality or complete verification.

| Technique | Development CLI coverage |
| --- | --- |
| BM25 lexical retrieval | Implemented. |
| Dense semantic retrieval | Implemented: exact cosine ranking, FastEmbed, Ollama, OpenAI-compatible providers. |
| Hybrid lexical + dense search | Implemented: weighted reciprocal rank fusion (RRF). |
| Recursive character splitting | Implemented for child retrieval, with size and overlap settings. |
| Markdown heading splitting | Implemented for child retrieval: ATX sections outside fenced code, with recursive size limits. Setext headings and language-specific parsers are not supported. |
| Overlapping chunks | Implemented for child retrieval; overlap counts characters and stays inside a Markdown section. |
| Parent-child retrieval | Implemented: search children, deduplicate and return original parent source units. |
| Cross-encoder reranking | Implemented through optional local FastEmbed models. |
| Multi-query retrieval | Implemented using supplied query variants, original-query inclusion, deduplication, and RRF. Automatic LLM generation of variants is missing. |
| Contextual retrieval | Partial: supplied, reviewed `metadata.context_prefix` is indexed before the body by BM25 and/or semantic search. Existing heading enrichment remains available. Automatic LLM prefix generation is missing. |
| Contextual compression | Missing: filtering/extraction that changes the final returned context needs evidence labels for the extracted passages. Reranking alone does not provide extraction. |
| Semantic chunking | Missing: embedding-based sentence boundary selection. |
| Code-aware splitting | Missing: language-aware syntax boundaries. |
| Late chunking | Missing: requires token-level embeddings and pooling interfaces. |
| Agentic/self-correcting RAG | Missing: relevance grading, bounded rewriting/retry, routing and abstention. |
| Query decomposition / multi-hop retrieval | Missing: fixed supplied query variants do not implement dependent retrieval steps. |
| GraphRAG / vector + graph retrieval | Missing: entity extraction, graph storage, source mappings, local/global graph search. |
| Multimodal RAG / ColPali | Missing: page/image ingestion, multivector representations, compatible late-interaction scoring and visual evidence evaluation. |
| Direct long-context comparison | Missing: a full-corpus generation baseline against retrieved context. |
| Approximate vector search / HNSW tuning | Missing: current dense search is exact and in memory; external ranked results can be imported. |
| Semantic answer caching | Missing. The existing embedding cache reuses indexing computation only. |
| Model-aware token budgets | Missing: runs record returned body character counts, not token counts or provider usage/cost. |
| Retrieval evaluation | Implemented: evidence sufficiency, coverage, rank metrics and regression comparison. |
| Answer correctness / citation / abstention evaluation | Missing: answer generation is for inspection. |

PDF loaders, OCR, production APIs, authorization, hosted tracing, Redis, Docker,
and infrastructure tuning are also discussed in the resource. They are not native
capabilities added by this change. Existing retriever imports can evaluate ranked
text source results from an external stack, provided IDs map to the workspace.

## Running an experiment

Create a workspace, then run one configuration:

```bash
ragvi init resource-lab
ragvi experiment workspaces/resource-lab docs/examples/parent-recursive.json
ragvi evaluate workspaces/resource-lab workspaces/resource-lab/runs/parent-recursive.json
ragvi report workspaces/resource-lab/evaluations/parent-recursive.json \
  workspaces/resource-lab/reports/parent-recursive.html --format html
```

Use `uv run ragvi` from the source checkout. Configuration paths shown here are
relative to the source archive. Installed tools can use equivalent user-written JSON.

`ragvi experiment WORKSPACE CONFIG_FILE` accepts the `StrategyConfig` JSON contract.
It runs once and refuses to replace an existing run. Run names use letters,
numbers, hyphens and underscores. Use distinct names when changing settings.
Existing `ragvi benchmark` remains available; it now accepts `--strategies hybrid`
and produces the usual body and heading-context runs.

### Configuration settings

| Key | Meaning / default |
| --- | --- |
| `name` | Required artifact name. |
| `strategy` | Required: `bm25`, `semantic`, or `hybrid`. |
| `representation` | `body` (default), `heading_context`, or `contextual`. |
| `k` | Final returned source depth; default 2. |
| `candidate_k` | Candidate depth before final selection. Default `k` for simple retrieval; `max(20, k)` when using hybrid, children, variants, or a reranker. Must be at least `k`. |
| `model`, `provider` | Semantic embedding configuration. Omitted values resolve from the existing environment settings and are recorded in the run. Hybrid uses them too. |
| `lexical_weight` | Hybrid BM25 contribution; default 0.5, strictly between 0 and 1. Dense weight is `1 - lexical_weight`. Use the corresponding single strategy for an endpoint weight. |
| `rrf_constant` | Rank smoothing constant; default 60, nonnegative. Distinct from retrieval depth. |
| `child_splitter` | `none` (default), `recursive`, or `markdown`. A non-`none` value enables parent-child retrieval. |
| `child_size`, `child_overlap` | Body character limits; defaults 500 and 50. Require `0 <= overlap < size`. Prefix text is additional to this body limit. |
| `query_variants` | Object mapping known question IDs to lists of nonblank alternate query strings. Default empty. |
| `reranker_model` | Optional FastEmbed cross-encoder model name. Default absent. |

Hybrid RRF sums `weight / (rrf_constant + rank)` for each source present in each
ranking. Ranks start at 1. Raw BM25 and cosine scores are not added. Each source
contributes at most once per list. Ties preserve first-seen order.

The pipeline order is: build representations → optionally split searchable
children → index → retrieve per query and fuse lexical/dense lists → return
deduplicated parents → fuse supplied query variants → optionally rerank candidates
against the original question → return at most `k` source units.

When several children match one parent, its best-ranked child supplies the parent
rank. Child candidate limits can return fewer than `k` unique parents. Increase
`candidate_k` to test this, while measuring the extra work. The same `candidate_k`
sets per-retriever and per-query candidate limits; it is not a total call budget.

### Query variants

`docs/examples/multiquery.json` uses the bundled `DEV-01` question. Replace IDs and
variants for your own workspace. The original question always participates;
duplicate strings are removed after trimming. Questions absent from the mapping
use their original query. Unknown IDs fail before indexing.

Write variants from the question alone, or generate them outside the evaluation
and review them. Do not use required evidence IDs or reference answers to tune
held-out variants. Runs record the queries actually searched. This supports
repeatable multi-query experiments without making additional LLM calls.

### Contextual prefixes

Add a reviewed description to every source's existing metadata:

```json
{"source_unit_id":"S-1","document_id":"manual","body":"Hold the button for eight seconds.","evidence_ids":["E-1"],"metadata":{"context_prefix":"Orion DeskHub firmware 4.2 pairing reset procedure."}}
```

Choose `"representation": "contextual"` in a configuration. Missing, blank, or
non-string prefixes fail explicitly. The body, source ID and evidence IDs stay
unchanged. Prefixes improve the searchable representation; their claims are not
automatically validated. Freeze prefixes before evaluating held-out questions.

### Local model dependencies

Hybrid semantic retrieval and cross-encoder reranking use the existing optional
dependency group:

```bash
uv sync --frozen --extra semantic
ragvi experiment workspaces/resource-lab docs/examples/hybrid.json
ragvi experiment workspaces/resource-lab docs/examples/reranked.json
```

FastEmbed downloads models on first use, then runs inference locally. Reranking
can also be used with a BM25 first stage. The CLI sends full candidate searchable
text to the reranker; the model's own input length and truncation rules still
apply. Relevance scores are not calibrated probabilities. The adapter follows
the [FastEmbed cross-encoder interface](https://qdrant.tech/documentation/fastembed/fastembed-rerankers/).
These features do not require a hosted model. Choosing a remote embedding
provider sends searchable text and original/alternate queries to that provider;
the CLI prints the disclosure before the run.

## Evidence and comparison limits

The labeled source unit is the parent. Child matches carry no inherited evidence
labels internally; the returned full parent supplies its reviewed evidence.
Metrics describe the entire returned parent context. They do not prove that the
matched child contains every required fact. Independent chunk-only evaluation
and compressed-context evaluation need finer reviewed evidence mappings and are
not provided here.

Compare the same dataset and `k`, changing one setting at a time. Parent expansion
can return more text at the same `k`; inspect `returned_context_characters` per
question. It counts body characters only, excluding headings, prompts and query
text, and is not a tokenizer or a model context-window check. Imported/older runs
without this measurement use `null`.

Runs and evaluations preserve resolved settings, searched queries, stage scores,
child offsets, warnings and character counts. JSON artifacts contain full
metadata; HTML and Markdown reports expose the full retrieval configuration and
warnings. There is no claim that a technique improves quality until measured on
your reviewed corpus. Deterministic tests exercise adapters and ranking behavior;
they do not establish a real model's retrieval or answer quality.
