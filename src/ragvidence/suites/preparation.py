"""Resolve bounded experiments and freeze original inputs before any model call."""

from pathlib import Path

from ragvidence.artifacts import content_hash, write_json
from ragvidence.budgets import tokenizer_hash
from ragvidence.capabilities import preset
from ragvidence.config import Settings
from ragvidence.ingestion import load_corpus
from ragvidence.ingestion.loaders import split_document
from ragvidence.ingestion.models import CorpusSnapshot
from ragvidence.models import SearchQuestion, StrategyConfig
from ragvidence.pipeline import resolve_config
from ragvidence.portable import create_output_directory, default_cache_dir
from ragvidence.portable_config import PortableOptions
from ragvidence.portable_inputs import load_variants
from ragvidence.reviewed import ReviewedReferences, load_reviewed
from ragvidence.suites.models import FrozenJob, FrozenShortlist, FrozenSuite, SuiteSpec
from ragvidence.suites.storage import file_digest, freeze_file, member, read_json

INGESTION_FIELDS = {
    "text_field",
    "include_patterns",
    "exclude_patterns",
    "max_files",
    "max_file_bytes",
    "max_total_bytes",
    "max_records",
    "max_extracted_characters",
}


def read_spec(path: Path) -> SuiteSpec:
    spec = SuiteSpec.model_validate(read_json(path))
    for variant in [*spec.variants, *(grid.variant for grid in spec.grids)]:
        for field in ("variants_file", "prefixes_file", "results_file", "usage_file"):
            value = getattr(variant, field)
            if value is not None:
                setattr(variant, field, (path.resolve().parent / value).resolve())
        if variant.options.get("tokenizer_file"):
            variant.options["tokenizer_file"] = str(
                (path.resolve().parent / variant.options["tokenizer_file"]).resolve()
            )
    spec.expanded()
    return spec


def provider_state(settings: Settings) -> str:
    return content_hash({"embedding_base_url": settings.embedding_base_url})


def rechunk(snapshot: CorpusSnapshot, size: int, overlap: int) -> CorpusSnapshot:
    preparation = snapshot.preparation.model_copy(
        update={"chunk_size": size, "chunk_overlap": overlap}
    )
    return snapshot.model_copy(
        update={
            "preparation": preparation,
            "passages": [
                passage
                for source in snapshot.documents
                for passage in split_document(source, size=size, overlap=overlap)
            ],
        }
    )


def effective_config(job: FrozenJob, questions: list[SearchQuestion]) -> StrategyConfig:
    ids = {question.question_id for question in questions}
    return job.config.model_copy(
        update={
            "query_variants": {
                key: values for key, values in job.config.query_variants.items() if key in ids
            }
        }
    )


def jobs_identity(jobs: list[FrozenJob]) -> str:
    values = []
    for job in jobs:
        value = job.model_dump(mode="json")
        value["config"].pop("tokenizer_file", None)
        values.append(value)
    return content_hash(values)


def check_policy(jobs: list[FrozenJob], policy: str) -> None:
    if policy == "fixed_k" and len({job.config.k for job in jobs}) != 1:
        raise ValueError("fixed_k requires the same final k; use descriptive for depth trade-offs")
    if policy == "fixed_tokens":
        signatures = {(job.config.context_budget, job.config.tokenizer_hash) for job in jobs}
        if len(signatures) != 1 or any(value is None for value in next(iter(signatures))):
            raise ValueError("fixed_tokens requires the same budget and identified local tokenizer")


def _copy_jobs(jobs: list[FrozenJob], old_root: Path, root: Path) -> list[FrozenJob]:
    def copy(relative):
        source = member(old_root, relative)
        if file_digest(source) != source.stem:
            raise ValueError("Frozen shortlist input changed")
        return freeze_file(root, source)

    copied = []
    for job in jobs:
        value = job.model_dump()
        for field in ("prefixes_file", "results_file", "usage_file"):
            if value[field]:
                value[field] = copy(value[field])
        if job.config.tokenizer_file:
            source = member(old_root, "inputs/" + Path(job.config.tokenizer_file).name)
            relative = copy(str(source.relative_to(old_root)))
            value["config"] = {
                **job.config.model_dump(),
                "tokenizer_file": str((root / relative).resolve()),
            }
        copied.append(FrozenJob.model_validate(value))
    return copied


def prepare_suite(
    source: Path,
    questions: list[SearchQuestion],
    options: PortableOptions,
    spec: SuiteSpec,
    settings: Settings,
    *,
    reviewed_file: Path | None = None,
    excluded: list[Path] | None = None,
    phase: str = "dev",
    shortlist: Path | None = None,
) -> tuple[Path, FrozenSuite, CorpusSnapshot, list[SearchQuestion], ReviewedReferences | None]:
    variants = spec.expanded() if shortlist is None else []
    selected = None
    if shortlist:
        selected = FrozenShortlist.model_validate(read_json(shortlist)).model_dump()
        selected_jobs = [FrozenJob.model_validate(value) for value in selected["jobs"]]
        if (
            selected.get("configuration_hash") != jobs_identity(selected_jobs)
            or selected.get("selection_phase") != "dev"
        ):
            raise ValueError("Shortlist configuration binding is invalid")
        spec = SuiteSpec.model_validate(selected["spec"])
        if reviewed_file is None:
            reviewed_file = member(shortlist.parent, "all-references.json")
    files = [*excluded] if excluded else []
    for variant in variants:
        files.extend(
            path
            for path in (
                variant.variants_file,
                variant.prefixes_file,
                variant.results_file,
                variant.usage_file,
            )
            if path
        )
        if variant.options.get("tokenizer_file"):
            files.append(Path(variant.options["tokenizer_file"]))
    snapshot = load_corpus(
        source,
        exclude=[
            options.output,
            options.cache_dir or default_cache_dir(),
            *([options.tokenizer_file] if options.tokenizer_file else []),
            *files,
            *([reviewed_file] if reviewed_file else []),
        ],
        size=options.chunk_size,
        overlap=options.chunk_overlap,
        **options.model_dump(include=INGESTION_FIELDS),
    )
    all_refs = load_reviewed(reviewed_file, snapshot) if reviewed_file else None
    if all_refs and questions:
        raise ValueError("Reviewed suites supply their own questions")
    if all_refs and phase in {"heldout", "all"} and shortlist is None:
        raise ValueError("Heldout evaluation requires a shortlist frozen from a dev comparison")
    references = (
        all_refs.model_copy(
            update={
                "questions": [q for q in all_refs.questions if phase == "all" or q.split == phase]
            }
        )
        if all_refs
        else None
    )
    if references and not references.questions:
        raise ValueError(f"No reviewed questions in phase {phase}")
    if references:
        questions = [
            SearchQuestion(question_id=q.question_id, question=q.question)
            for q in references.questions
        ]
    known = {q.question_id for q in (all_refs.questions if all_refs else questions)}
    if spec.question_groups.keys() - known:
        raise ValueError("Question grouping contains unknown question IDs")
    if all_refs and any(
        len([tag for tag in q.tags if tag.startswith("family:")]) > 1
        and q.question_id not in spec.question_groups
        for q in all_refs.questions
    ):
        raise ValueError("Declare one family: tag or an explicit question group")
    if selected and (
        selected["corpus_hash"] != snapshot.corpus_hash
        or selected["references_hash"] != all_refs.identity
    ):
        raise ValueError("Shortlist does not match this corpus and complete reviewed references")
    if selected and selected.get("provider_state_hash") != provider_state(settings):
        raise ValueError("Provider endpoint differs from the frozen shortlist")
    root = create_output_directory(options.output, "comparison-" + source.stem)
    write_json(root / "snapshot.json", snapshot)
    write_json(root / "questions.json", questions)
    if all_refs:
        write_json(root / "all-references.json", all_refs)
    if references:
        write_json(root / "references.json", references)
    jobs = []
    for variant in variants:
        allowed = {
            "k",
            "base_retriever",
            "model",
            "provider",
            "representation",
            "reranker_model",
            "branch_k",
            "child_k",
            "query_k",
            "rerank_k",
            "context_budget",
            "tokenizer_file",
            "lexical_weight",
            "rrf_constant",
            "chunk_size",
            "chunk_overlap",
            "child_splitter",
        }
        if variant.options.keys() - allowed:
            raise ValueError("Variant options may only change retrieval or chunk parameters")
        merged = PortableOptions.model_validate({**options.model_dump(), **variant.options})
        config = preset(variant.technique, merged, variants=load_variants(variant.variants_file))
        config = config.model_copy(update={"name": variant.name})
        if config.query_variants.keys() - known:
            raise ValueError("Query variants contain unknown question IDs")
        if config.tokenizer_file:
            relative = freeze_file(root, Path(config.tokenizer_file))
            config = config.model_copy(
                update={
                    "tokenizer_file": str((root / relative).resolve()),
                    "tokenizer_hash": tokenizer_hash(str(root / relative)),
                }
            )
        if config.strategy != "imported":
            config = resolve_config(config, settings)
        jobs.append(
            FrozenJob(
                name=variant.name,
                config=config,
                chunk_size=merged.chunk_size,
                chunk_overlap=merged.chunk_overlap,
                **{
                    field: freeze_file(root, path) if path else None
                    for field, path in {
                        "prefixes_file": variant.prefixes_file,
                        "results_file": variant.results_file,
                        "usage_file": variant.usage_file,
                    }.items()
                },
            )
        )
    if selected:
        jobs = _copy_jobs(selected_jobs, shortlist.parent, root)
    check_policy(jobs, spec.policy)
    call_bound = sum(
        sum(1 + len(set(job.config.query_variants.get(q.question_id, []))) for q in questions)
        * (2 if job.config.strategy == "hybrid" else 1)
        + len(questions) * bool(job.config.reranker_model)
        for job in jobs
        if job.config.strategy != "imported"
    ) * (1 + spec.warm_repeats)
    if call_bound > spec.max_query_calls:
        raise ValueError("Suite exceeds max_query_calls before execution")
    heldout_use = {}
    if references and phase in {"heldout", "all"}:
        identity = content_hash({"corpus": snapshot.corpus_hash, "references": all_refs.identity})
        ledger = options.output / ".heldout-uses" / identity
        while True:
            previous = max(
                (int(path.stem) for path in ledger.glob("*.json") if path.stem.isdigit()), default=0
            )
            heldout_use = {
                "evaluation_number": previous + 1,
                "reused": previous > 0,
                "scope": "this output root",
                "shortlist_hash": selected["configuration_hash"],
                "evaluation_identity": identity,
            }
            try:
                write_json(ledger / f"{previous + 1:08d}.json", heldout_use)
                break
            except FileExistsError:
                continue
    frozen_files = {
        str(path.relative_to(root)): file_digest(path)
        for path in root.rglob("*")
        if path.is_file() and path.name != ".ragvi-run.json"
    }
    plan = FrozenSuite(
        input_name=source.name,
        phase=phase,
        spec=spec,
        jobs=jobs,
        baseline=(selected["baseline"] if selected else spec.baseline) or jobs[0].name,
        snapshot_hash=content_hash(snapshot),
        questions_hash=content_hash(questions),
        references_hash=references.identity if references else None,
        all_references_hash=all_refs.identity if all_refs else None,
        files=frozen_files,
        provider_state_hash=provider_state(settings),
        query_call_upper_bound=call_bound,
        heldout_use=heldout_use,
    )
    write_json(root / "suite.json", plan)
    write_json(root / "plan-hash.json", {"hash": content_hash(plan)})
    return root, plan, snapshot, questions, references
