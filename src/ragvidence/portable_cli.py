"""Thin portable CLI entry points backed by the shared application service."""

import sys
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragvidence.models import StrategyConfig
from ragvidence.portable import normalize_formats, run_portable
from ragvidence.questions import load_questions


def input_is_terminal() -> bool:
    return sys.stdin.isatty()


def register_portable_commands(app: typer.Typer, console: Console) -> None:
    @app.command("bm25")
    def bm25(
        input_path: Annotated[
            Path, typer.Argument(metavar="INPUT", help="TXT/Markdown file or folder")
        ],
        query: Annotated[
            list[str] | None, typer.Option("--query", help="Search question; repeatable")
        ] = None,
        questions: Annotated[Path | None, typer.Option(help="TXT, JSON or JSONL questions")] = None,
        format: Annotated[
            list[str] | None, typer.Option("--format", help="html, json or markdown")
        ] = None,
        output: Annotated[Path, typer.Option(help="Report output root")] = Path("ragvi-reports"),
        cache_dir: Annotated[Path | None, typer.Option()] = None,
        k: Annotated[int, typer.Option(min=1)] = 2,
        chunk_size: Annotated[
            int, typer.Option(min=1, help="Maximum passage body characters")
        ] = 500,
        chunk_overlap: Annotated[int, typer.Option(min=0)] = 50,
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
            formats = normalize_formats(format)
            if chunk_overlap >= chunk_size:
                raise ValueError("chunk-overlap must be smaller than chunk-size")
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
                StrategyConfig(name="bm25", strategy="bm25", k=k),
                output_root=output,
                formats=formats,
                question_file=questions,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                cache_dir=cache_dir,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            console.print(f"FAIL {exc}", markup=False)
            raise typer.Exit(1) from exc
        report = result.report
        info = report["input"]
        console.print(f"COMPLETE · {report['evaluation_level']}", markup=False)
        console.print(
            f"{info['document_count']} sources · {info['passage_count']} passages · "
            f"{len(report['questions'])} questions · {len(info['skipped'])} skipped",
            markup=False,
        )
        for observation in report["observations"]:
            console.print(observation, markup=False)
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
