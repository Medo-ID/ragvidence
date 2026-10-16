"""Translate shared portable CLI options into a bounded comparison request."""

from pathlib import Path

from ragvidence.suites.execution import compare_data
from ragvidence.suites.models import SuiteSpec, Variant
from ragvidence.suites.preparation import read_spec


def run_comparison_cli(
    source,
    questions,
    options,
    settings,
    *,
    techniques: str | None = None,
    suite_file: Path | None = None,
    baseline: str | None = None,
    policy: str | None = None,
    phase: str = "dev",
    shortlist: Path | None = None,
    shortlist_names: str | None = None,
    resume: Path | None = None,
    warm_repeats: int | None = None,
    bootstrap_samples: int | None = None,
    bootstrap_seed: int | None = None,
    reviewed=None,
    variants=None,
    prefixes=None,
    results=None,
    excluded=None,
    on_event=None,
):
    if phase not in {"dev", "heldout", "all"}:
        raise ValueError("phase must be dev, heldout or all")
    if resume and any(
        value is not None
        for value in (
            techniques,
            suite_file,
            baseline,
            policy,
            shortlist,
            shortlist_names,
            warm_repeats,
            bootstrap_samples,
            bootstrap_seed,
            reviewed,
            variants,
            prefixes,
            results,
        )
    ):
        raise ValueError(
            "Resume uses its frozen plan; supply only output formats, cache/env and --resume"
        )
    if shortlist and (suite_file or techniques):
        raise ValueError("--shortlist freezes configurations; omit --suite/--techniques")
    if suite_file and techniques:
        raise ValueError("Use --suite or --techniques")
    spec = read_spec(suite_file) if suite_file else SuiteSpec()
    if not suite_file and not shortlist and not resume:
        names = [name.strip() for name in (techniques or "bm25,parent-child").split(",")]
        if any(not name for name in names):
            raise ValueError("--techniques must contain nonempty names")
        spec.variants = [
            Variant(
                name=name,
                technique=name,
                options={
                    "reranker_model": options.reranker_model if name == "rerank" else None,
                    "filters": options.filters.model_dump()
                    if name == "metadata-filter" and options.filters
                    else None,
                    "mmr": options.mmr.model_dump() if name == "mmr" and options.mmr else None,
                    "rewrite": {
                        **options.rewrite.model_dump(),
                        "count": 1 if name == "rewrite" else options.rewrite.count,
                    }
                    if name in {"rewrite", "auto-multi-query"} and options.rewrite
                    else None,
                    "compression": options.compression.model_dump()
                    if name == "compress" and options.compression
                    else None,
                },
                variants_file=variants if name == "multi-query" else None,
                prefixes_file=prefixes if name == "contextual" else None,
            )
            for name in names
        ]
    if results:
        if suite_file:
            raise ValueError("Declare imported baseline results inside the suite file")
        spec.variants.insert(
            0,
            Variant(
                name="existing",
                technique="import-data",
                results_file=results,
                options={
                    "reranker_model": None,
                    "filters": None,
                    "mmr": None,
                    "rewrite": None,
                    "compression": None,
                },
            ),
        )
    overrides = {
        key: value
        for key, value in {
            "baseline": baseline,
            "policy": policy,
            "warm_repeats": warm_repeats,
            "bootstrap_samples": bootstrap_samples,
            "bootstrap_seed": bootstrap_seed,
        }.items()
        if value is not None
    }
    spec = SuiteSpec.model_validate({**spec.model_dump(), **overrides})
    return compare_data(
        source,
        questions,
        options,
        spec,
        settings,
        reviewed_file=reviewed,
        excluded=[*(excluded or []), *([suite_file] if suite_file else [])],
        phase=phase,
        shortlist=shortlist,
        shortlist_names=[name.strip() for name in shortlist_names.split(",")]
        if shortlist_names
        else None,
        resume=resume,
        on_event=on_event,
    )


def print_comparison(console, report):
    console.print(
        f"{report['state'].upper()} · {report['evaluation_level']} · "
        f"policy={report['policy']} · phase={report['phase']}",
        markup=False,
    )
    for entry in report["participants"]:
        console.print(f"{entry['name']}: {entry['state']}", markup=False)
        if entry["state"] != "complete":
            console.print(entry["error"], markup=False)
            continue
        for split, scopes in entry["summaries"].items():
            summary = scopes["all"]
            console.print(
                f"  {split}: {summary['sufficient_count']}/{summary['answerable_questions']} "
                "answerable questions sufficient",
                markup=False,
            )
        resource = entry["resources"]
        console.print(
            f"  Query ms (known): {resource['query_ms']['mean_known']} · "
            f"Context: {resource['context_units']['mean_known']} {resource['context_unit']}",
            markup=False,
        )
    for observation in report["observations"]:
        console.print(observation, markup=False)
