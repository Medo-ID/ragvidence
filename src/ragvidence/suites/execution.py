"""Run/resume frozen suites using the same application service as single commands."""

from pathlib import Path
from uuid import uuid4

from ragvidence.artifacts import write_json, write_text
from ragvidence.config import Settings
from ragvidence.models import SearchQuestion
from ragvidence.portable import (
    PortableResult,
    create_output_directory,
    default_cache_dir,
    execute_snapshot,
    normalize_formats,
)
from ragvidence.portable_config import PortableOptions
from ragvidence.reporting.render import render_report
from ragvidence.suites.models import SuiteSpec
from ragvidence.suites.preparation import (
    effective_config,
    jobs_identity,
    prepare_suite,
    provider_state,
    rechunk,
)
from ragvidence.suites.report import build_comparison
from ragvidence.suites.resources import resources, supplied_cost
from ragvidence.suites.storage import member, read_json, seal_attempt
from ragvidence.suites.validation import load_frozen, validate_completed


def compare_data(
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
    shortlist_names: list[str] | None = None,
    resume: Path | None = None,
    on_event=None,
) -> PortableResult:
    formats = normalize_formats(options.formats)
    if resume:
        root = resume
        plan, snapshot, questions, references = load_frozen(root)
        if provider_state(settings) != plan.provider_state_hash:
            raise ValueError(
                "Provider endpoint changed; start a fresh comparison instead of resuming"
            )
    else:
        root, plan, snapshot, questions, references = prepare_suite(
            source,
            questions,
            options,
            spec,
            settings,
            reviewed_file=reviewed_file,
            excluded=excluded,
            phase=phase,
            shortlist=shortlist,
        )
    if shortlist_names is not None and (
        not references
        or plan.phase != "dev"
        or not shortlist_names
        or len(set(shortlist_names)) != len(shortlist_names)
        or set(shortlist_names) - {job.name for job in plan.jobs}
        or plan.baseline not in shortlist_names
    ):
        raise ValueError(
            "Dev shortlist names must select unique configurations including the baseline"
        )
    entries = []
    all_ids = (
        {value["question_id"] for value in read_json(root / "all-references.json")["questions"]}
        if plan.all_references_hash
        else {q.question_id for q in questions}
    )
    for job in plan.jobs:
        if on_event:
            config = job.config
            if questions and config.strategy in {"semantic", "hybrid"}:
                on_event(
                    {
                        "message": f"DISCLOSURE: {config.provider} receives source text/queries."
                        if config.provider != "fastembed"
                        else "Local embedding models may download on first use."
                    }
                )
            if questions and config.reranker_model:
                on_event({"message": "Local reranking model may download on first use."})
            on_event({"message": f"Comparing {job.name}"})
        prepared = rechunk(snapshot, job.chunk_size, job.chunk_overlap)
        trials = []
        error = None
        for trial in range(plan.spec.warm_repeats + 1):
            parent = root / "jobs" / job.name / f"trial-{trial}"
            completed = sorted(parent.glob("*/checkpoint.json"))
            if len(completed) > 1:
                raise ValueError("Multiple completed attempts for the same frozen trial")
            config = effective_config(job, questions)
            if completed:
                directory = completed[0].parent
                report = validate_completed(directory, prepared, questions, references, job)
                reused = True
            else:
                directory = create_output_directory(parent, "attempt")
                try:
                    result = execute_snapshot(
                        prepared,
                        questions,
                        config,
                        output_root=root,
                        name=plan.input_name,
                        directory=directory,
                        store_inputs=False,
                        formats=["json"],
                        references=references,
                        settings=settings,
                        cache_dir=options.cache_dir or default_cache_dir(),
                        prefixes_file=member(root, job.prefixes_file)
                        if job.prefixes_file
                        else None,
                        results_file=member(root, job.results_file) if job.results_file else None,
                        known_question_ids=all_ids,
                    )
                    report = result.report
                    seal_attempt(directory)
                    reused = False
                except (OSError, ValueError, RuntimeError) as exc:
                    error = str(exc)
                    if not (directory / "status.json").exists():
                        write_json(directory / "status.json", {"state": "failed", "error": error})
                    write_json(
                        root / "events" / (uuid4().hex + ".json"),
                        {"job": job.name, "trial": trial, "state": "failed", "error": error},
                    )
                    break
            trials.append(
                {
                    "trial": trial,
                    "reused": reused,
                    "artifact_directory": str(directory.relative_to(root)),
                    "resources": resources(report),
                    "report": report,
                }
            )
        if not trials:
            entries.append({"name": job.name, "state": "failed", "error": error, "trials": []})
            continue
        primary = trials[0]
        try:
            cost = supplied_cost(
                member(root, job.usage_file) if job.usage_file else None,
                plan.spec.pricing,
                {q.question_id for q in questions},
                all_ids,
            )
        except (OSError, ValueError) as exc:
            entries.append({"name": job.name, "state": "failed", "error": str(exc), "trials": []})
            continue
        entries.append(
            {
                "name": job.name,
                "state": "complete" if error is None else "partial_failure",
                "error": error,
                "report": primary["report"],
                "resources": primary["resources"],
                "usage": cost,
                "trials": [
                    {key: value for key, value in item.items() if key != "report"}
                    for item in trials
                ],
                "repeat_rankings_changed": any(
                    [q["context_hash"] for q in item["report"]["questions"]]
                    != [q["context_hash"] for q in primary["report"]["questions"]]
                    for item in trials[1:]
                ),
            }
        )
    report = build_comparison(plan, entries, resumed=resume is not None)
    if references and plan.phase == "dev" and not (root / "shortlist.json").exists():
        successful = {entry["name"] for entry in entries if entry["state"] == "complete"}
        names = shortlist_names or [
            entry["name"] for entry in entries if entry["state"] == "complete"
        ]
        if names and plan.baseline in names and not set(names) - successful:
            jobs = [job for job in plan.jobs if job.name in names]
            if len(jobs) != len(set(names)):
                raise ValueError("Shortlist names must select completed configurations")
            write_json(
                root / "shortlist.json",
                {
                    "schema_version": 1,
                    "selection_phase": "dev",
                    "configuration_hash": jobs_identity(jobs),
                    "jobs": jobs,
                    "baseline": plan.baseline,
                    "spec": plan.spec,
                    "corpus_hash": snapshot.corpus_hash,
                    "references_hash": plan.all_references_hash,
                    "provider_state_hash": plan.provider_state_hash,
                },
            )
        elif shortlist_names:
            report["observations"].append(
                "Shortlist was not frozen because a selected configuration failed."
            )
    export_root = root / "exports" / uuid4().hex
    exports = {}
    for format in formats:
        path = export_root / f"report.{'md' if format == 'markdown' else format}"
        write_text(path, render_report(report, format))
        exports[format] = path
    write_json(
        root / "events" / (uuid4().hex + ".json"),
        {
            "state": report["state"],
            "resumed": resume is not None,
            "report_files": {name: str(path.relative_to(root)) for name, path in exports.items()},
        },
    )
    return PortableResult(root, report, exports)
