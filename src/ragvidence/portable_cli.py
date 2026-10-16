"""Thin portable CLI entry points backed by the shared application service."""

import sys
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragvidence.capabilities import CAPABILITIES, catalog, preset
from ragvidence.config import Settings
from ragvidence.portable import normalize_formats, run_portable
from ragvidence.portable_config import resolve_portable_options
from ragvidence.portable_inputs import load_variants
from ragvidence.questions import load_questions
from ragvidence.suites.cli import print_comparison, run_comparison_cli


def input_is_terminal() -> bool:
    return sys.stdin.isatty()


def register_portable_commands(app: typer.Typer, console: Console) -> None:
    def inspect(
        ctx: typer.Context,
        input_path: Annotated[
            Path,
            typer.Argument(
                metavar="INPUT", help="TXT, Markdown, HTML, JSON, JSONL, CSV or PDF input"
            ),
        ],
        query: Annotated[
            list[str] | None, typer.Option("--query", help="Search question; repeatable")
        ] = None,
        questions: Annotated[Path | None, typer.Option(help="TXT, JSON or JSONL questions")] = None,
        reviewed: Annotated[
            Path | None, typer.Option(help="Reviewed questions and original evidence spans")
        ] = None,
        variants: Annotated[Path | None, typer.Option(help="Supplied query variants JSON")] = None,
        prefixes: Annotated[
            Path | None, typer.Option(help="Reviewed contextual prefixes JSON")
        ] = None,
        results: Annotated[
            Path | None, typer.Option(help="External results JSONL for import-data")
        ] = None,
        base_retriever: Annotated[
            str | None, typer.Option(help="Base for modifiers: bm25, semantic, hybrid")
        ] = None,
        provider: Annotated[
            str | None, typer.Option(help="fastembed, ollama, openai_compatible")
        ] = None,
        model: Annotated[str | None, typer.Option(help="Embedding model")] = None,
        lexical_weight: Annotated[
            float | None, typer.Option(help="Hybrid lexical weight, between zero and one")
        ] = None,
        rrf_constant: Annotated[
            int | None, typer.Option(min=0, help="Reciprocal rank fusion constant")
        ] = None,
        reranker_model: Annotated[
            str | None, typer.Option(help="Local cross-encoder model")
        ] = None,
        representation: Annotated[
            str | None, typer.Option(help="body, heading_context, contextual")
        ] = None,
        child_splitter: Annotated[str | None, typer.Option(help="recursive or markdown")] = None,
        branch_k: Annotated[
            int | None, typer.Option(min=1, help="Candidates per hybrid branch")
        ] = None,
        child_k: Annotated[
            int | None, typer.Option(min=1, help="Children searched before parent deduplication")
        ] = None,
        query_k: Annotated[
            int | None, typer.Option(min=1, help="Results per supplied search query")
        ] = None,
        rerank_k: Annotated[
            int | None, typer.Option(min=1, help="Maximum candidates scored by reranker")
        ] = None,
        context_budget: Annotated[
            int | None,
            typer.Option(
                min=1, help="Rendered context characters, or tokens with --tokenizer-file"
            ),
        ] = None,
        tokenizer_file: Annotated[
            Path | None,
            typer.Option(help="Local Hugging Face tokenizer.json for exact context counting"),
        ] = None,
        format: Annotated[
            list[str] | None, typer.Option("--format", help="html, json or markdown")
        ] = None,
        output: Annotated[Path | None, typer.Option(help="Report output root")] = None,
        cache_dir: Annotated[Path | None, typer.Option()] = None,
        config_file: Annotated[
            Path | None, typer.Option("--config", help="Portable TOML/JSON options")
        ] = None,
        env_file: Annotated[
            Path | None, typer.Option(help="Explicit dotenv file; never discovered automatically")
        ] = None,
        text_field: Annotated[
            str | None, typer.Option(help="Document text field/CSV column")
        ] = None,
        include: Annotated[
            list[str] | None, typer.Option("--include", help="Relative path glob; repeatable")
        ] = None,
        exclude: Annotated[
            list[str] | None, typer.Option("--exclude", help="Relative path glob; repeatable")
        ] = None,
        max_files: Annotated[int | None, typer.Option(min=1)] = None,
        max_file_bytes: Annotated[int | None, typer.Option(min=1)] = None,
        max_total_bytes: Annotated[int | None, typer.Option(min=1)] = None,
        max_records: Annotated[
            int | None, typer.Option(min=1, help="Records/sections/pages per file")
        ] = None,
        max_extracted_characters: Annotated[
            int | None, typer.Option(min=1, help="Total extracted character limit")
        ] = None,
        k: Annotated[int | None, typer.Option(min=1)] = None,
        chunk_size: Annotated[
            int | None, typer.Option(min=1, help="Maximum passage body characters")
        ] = None,
        chunk_overlap: Annotated[int | None, typer.Option(min=0)] = None,
        techniques: Annotated[
            str | None, typer.Option(help="Comparison techniques, comma separated")
        ] = None,
        suite_file: Annotated[
            Path | None, typer.Option("--suite", help="Advanced comparison suite JSON")
        ] = None,
        baseline: Annotated[
            str | None, typer.Option(help="Comparison baseline configuration name")
        ] = None,
        policy: Annotated[
            str | None, typer.Option(help="fixed_k, fixed_tokens or descriptive comparison")
        ] = None,
        phase: Annotated[
            str, typer.Option(help="dev, heldout or all; heldout needs a frozen shortlist")
        ] = "dev",
        shortlist: Annotated[
            Path | None, typer.Option(help="Frozen dev shortlist for heldout evaluation")
        ] = None,
        shortlist_names: Annotated[
            str | None, typer.Option(help="Dev configurations to freeze, comma separated")
        ] = None,
        resume: Annotated[
            Path | None, typer.Option(help="Resume a frozen comparison directory")
        ] = None,
        warm_repeats: Annotated[int | None, typer.Option(min=0, max=3)] = None,
        bootstrap_samples: Annotated[int | None, typer.Option(min=100, max=10000)] = None,
        bootstrap_seed: Annotated[int | None, typer.Option(min=0)] = None,
        no_input: Annotated[
            bool, typer.Option("--no-input", help="Never prompt for input")
        ] = False,
        interactive: Annotated[
            bool, typer.Option("--interactive", help="Offer report format selection")
        ] = False,
        open_report: Annotated[
            bool, typer.Option("--open", help="Open saved HTML in a browser")
        ] = False,
    ) -> None:
        """Diagnose this technique on local data and export traceable evidence."""
        try:
            options = resolve_portable_options(
                {
                    "output": output,
                    "cache_dir": cache_dir,
                    "formats": format,
                    "k": k,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "text_field": text_field,
                    "include_patterns": include,
                    "exclude_patterns": exclude,
                    "max_files": max_files,
                    "max_file_bytes": max_file_bytes,
                    "max_total_bytes": max_total_bytes,
                    "max_records": max_records,
                    "max_extracted_characters": max_extracted_characters,
                    "base_retriever": base_retriever,
                    "provider": provider,
                    "model": model,
                    "lexical_weight": lexical_weight,
                    "rrf_constant": rrf_constant,
                    "reranker_model": reranker_model,
                    "representation": representation,
                    "child_splitter": child_splitter,
                    "branch_k": branch_k,
                    "child_k": child_k,
                    "query_k": query_k,
                    "rerank_k": rerank_k,
                    "context_budget": context_budget,
                    "tokenizer_file": tokenizer_file,
                },
                config_file=config_file,
                env_file=env_file,
            )
            formats = normalize_formats(options.formats)
            if interactive and (no_input or not input_is_terminal()):
                raise ValueError("--interactive requires terminal input and cannot use --no-input")
            if reviewed and (query or questions):
                raise ValueError(
                    "--reviewed supplies questions; do not combine with --query/--questions"
                )
            search_questions = load_questions(query or [], questions)
            if (
                not reviewed
                and not shortlist
                and not resume
                and not search_questions
                and not no_input
                and input_is_terminal()
            ):
                entered = typer.prompt(
                    "Question (leave empty for source diagnostics)", default="", show_default=False
                )
                if entered.strip():
                    search_questions = load_questions([entered], None)
            if interactive and format is None:
                selected = typer.prompt("Report format(s): html, json, markdown", default="html")
                formats = normalize_formats([value.strip() for value in selected.split(",")])
            if open_report and "html" not in formats:
                raise ValueError("--open requires an HTML report; add --format html")
            if ctx.command.name == "compare-data":
                if shortlist:
                    frozen_parameters = {
                        "techniques",
                        "suite_file",
                        "baseline",
                        "policy",
                        "warm_repeats",
                        "bootstrap_seed",
                        "bootstrap_samples",
                        "model",
                        "provider",
                        "reranker_model",
                        "representation",
                        "child_splitter",
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
                        "base_retriever",
                        "variants",
                        "prefixes",
                        "results",
                    }
                    if any(
                        ctx.get_parameter_source(name)
                        and ctx.get_parameter_source(name).name == "COMMANDLINE"
                        for name in frozen_parameters
                    ):
                        raise ValueError(
                            "Shortlist freezes configurations; omit retrieval/comparison overrides"
                        )
                if resume:
                    allowed = {
                        "input_path",
                        "resume",
                        "format",
                        "cache_dir",
                        "env_file",
                        "no_input",
                        "open_report",
                    }
                    provided = {
                        name
                        for name in ctx.params
                        if ctx.get_parameter_source(name)
                        and ctx.get_parameter_source(name).name == "COMMANDLINE"
                    }
                    if provided - allowed:
                        raise ValueError(
                            "Resume uses frozen options; omit configuration/question overrides"
                        )
                if resume and (query or questions):
                    raise ValueError("Resume uses frozen questions; omit --query/--questions")
                result = run_comparison_cli(
                    input_path,
                    search_questions,
                    options,
                    Settings(_env_file=env_file),
                    techniques=techniques,
                    suite_file=suite_file,
                    baseline=baseline,
                    policy=policy,
                    phase=phase,
                    shortlist=shortlist,
                    shortlist_names=shortlist_names,
                    resume=resume,
                    warm_repeats=warm_repeats,
                    bootstrap_samples=bootstrap_samples,
                    bootstrap_seed=bootstrap_seed,
                    reviewed=reviewed,
                    variants=variants,
                    prefixes=prefixes,
                    results=results,
                    excluded=[
                        path
                        for path in (
                            config_file,
                            env_file,
                            questions,
                            variants,
                            prefixes,
                            results,
                            options.tokenizer_file,
                        )
                        if path is not None
                    ],
                    on_event=lambda event: console.print(event["message"], markup=False),
                )
            else:
                if (
                    ctx.get_parameter_source("phase")
                    and ctx.get_parameter_source("phase").name == "COMMANDLINE"
                ):
                    raise ValueError("--phase requires compare-data")
                if any(
                    value is not None
                    for value in (
                        techniques,
                        suite_file,
                        baseline,
                        policy,
                        shortlist,
                        shortlist_names,
                        resume,
                        warm_repeats,
                        bootstrap_samples,
                        bootstrap_seed,
                    )
                ):
                    raise ValueError("Comparison options require compare-data")
                config = preset(ctx.command.name, options, variants=load_variants(variants))
                settings = Settings(_env_file=env_file)
                if (search_questions or reviewed) and config.strategy in {"semantic", "hybrid"}:
                    selected_provider = config.provider or settings.embedding_provider
                    if selected_provider != "fastembed":
                        console.print(
                            f"DISCLOSURE: {selected_provider} receives source text "
                            "and search queries.",
                            markup=False,
                        )
                    else:
                        console.print(
                            "Local embeddings may download the selected model on first use."
                        )
                if (search_questions or reviewed) and config.reranker_model:
                    console.print("Local reranking may download the selected model on first use.")
                result = run_portable(
                    input_path,
                    search_questions,
                    config,
                    output_root=options.output,
                    formats=formats,
                    question_file=questions,
                    chunk_size=options.chunk_size,
                    chunk_overlap=options.chunk_overlap,
                    cache_dir=options.cache_dir,
                    ingestion_options=options.model_dump(
                        include={
                            "text_field",
                            "include_patterns",
                            "exclude_patterns",
                            "max_files",
                            "max_file_bytes",
                            "max_total_bytes",
                            "max_records",
                            "max_extracted_characters",
                        }
                    ),
                    excluded_inputs=[
                        path
                        for path in (config_file, env_file, variants, options.tokenizer_file)
                        if path is not None
                    ],
                    settings=settings,
                    reviewed_file=reviewed,
                    prefixes_file=prefixes,
                    results_file=results,
                )
        except (OSError, ValueError, RuntimeError) as exc:
            console.print(f"FAIL {exc}", markup=False)
            raise typer.Exit(1) from exc
        report = result.report
        if report.get("kind") == "comparison":
            print_comparison(console, report)
            console.print(
                f"Comparison artifacts: {result.directory.resolve()}", markup=False, soft_wrap=True
            )
            if (result.directory / "shortlist.json").exists():
                console.print(
                    f"Frozen shortlist: {(result.directory / 'shortlist.json').resolve()}",
                    markup=False,
                    soft_wrap=True,
                )
        else:
            info = report["input"]
            console.print(f"COMPLETE · {report['evaluation_level']}", markup=False)
            console.print(
                f"{info['document_count']} sources · {info['passage_count']} passages · "
                f"{len(report['questions'])} questions · {info['skipped_count']} skipped · "
                f"{info['failed_count']} failed · {info['warning_count']} warnings",
                markup=False,
            )
            for observation in report["observations"]:
                console.print(observation, markup=False)
            for notice in info["skipped"]:
                console.print(
                    f"{notice['kind'].upper()} {notice['path']}: {notice['reason']}", markup=False
                )
            for question in report["questions"]:
                console.print(f"\n{question['question']}", markup=False)
                if question["metrics"]:
                    row = question["metrics"]
                    sufficient = (
                        "N/A" if row["sufficient_evidence"] is None else row["sufficient_evidence"]
                    )
                    coverage = (
                        "N/A" if row["evidence_coverage"] is None else row["evidence_coverage"]
                    )
                    console.print(
                        f"Sufficient evidence: {sufficient} · "
                        f"Coverage: {coverage} · "
                        f"Missing: {', '.join(row['missing_evidence_ids']) or 'none'}",
                        markup=False,
                    )
                for hit in question["hits"]:
                    console.print(
                        f"  #{hit['rank']} {hit['source_path']} · {hit['score']:.4f}\n"
                        f"  {hit['text'][:240]}",
                        markup=False,
                    )
        for format_name, path in result.exports.items():
            console.print(
                f"{format_name.upper()} report: {path.resolve()}", markup=False, soft_wrap=True
            )
        if open_report:
            try:
                opened = webbrowser.open(result.exports["html"].resolve().as_uri())
                if not opened:
                    console.print("Browser unavailable; open the saved HTML report manually.")
            except (OSError, webbrowser.Error):
                console.print("Browser unavailable; open the saved HTML report manually.")
        if report.get("kind") == "comparison" and report["state"] != "complete":
            raise typer.Exit(1)

    for capability in CAPABILITIES:
        app.command(capability.name, help=capability.description)(inspect)
    app.command(
        "compare-data", help="Compare techniques on one frozen corpus and export decision evidence"
    )(inspect)

    @app.command("techniques")
    def techniques(format: Annotated[str, typer.Option(help="terminal or json")] = "terminal"):
        """List the implemented portable techniques and prerequisites."""
        import json

        if format == "json":
            console.print(
                json.dumps(catalog(), indent=2), markup=False, highlight=False, soft_wrap=True
            )
        elif format == "terminal":
            for capability in CAPABILITIES:
                console.print(
                    f"{capability.name}: {capability.description}\n"
                    f"  Requires: {capability.requirements}",
                    markup=False,
                )
        else:
            console.print("FAIL Supported catalog formats: terminal, json")
            raise typer.Exit(1)
