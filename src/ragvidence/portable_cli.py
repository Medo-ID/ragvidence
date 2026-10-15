"""Thin portable CLI entry points backed by the shared application service."""

import sys
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragvidence.config import Settings
from ragvidence.models import StrategyConfig
from ragvidence.portable import normalize_formats, run_portable
from ragvidence.portable_config import resolve_portable_options
from ragvidence.questions import load_questions


def input_is_terminal() -> bool:
    return sys.stdin.isatty()


def register_portable_commands(app: typer.Typer, console: Console) -> None:
    @app.command("bm25")
    def bm25(
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
        """Inspect BM25 on local data and save a report without project setup."""
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
                },
                config_file=config_file,
                env_file=env_file,
            )
            formats = normalize_formats(options.formats)
            if interactive and (no_input or not input_is_terminal()):
                raise ValueError("--interactive requires terminal input and cannot use --no-input")
            search_questions = load_questions(query or [], questions)
            if not search_questions and not no_input and input_is_terminal():
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
            result = run_portable(
                input_path,
                search_questions,
                StrategyConfig(name="bm25", strategy="bm25", k=options.k),
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
                excluded_inputs=[path for path in (config_file, env_file) if path is not None],
                settings=Settings(_env_file=env_file),
            )
        except (OSError, ValueError, RuntimeError) as exc:
            console.print(f"FAIL {exc}", markup=False)
            raise typer.Exit(1) from exc
        report = result.report
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
