"""Command-line interface for local evidence-level RAG experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ragvidence import __edition__, __version__
from ragvidence.artifacts import write_json, write_text
from ragvidence.comparison import compare_evaluations
from ragvidence.data import DatasetError, load_dataset
from ragvidence.diagnosis import diagnose as build_diagnosis
from ragvidence.evaluation.evaluator import evaluate_run
from ragvidence.generation import generate_answers
from ragvidence.health import run_health
from ragvidence.importer import import_retrieval_run
from ragvidence.models import ExperimentRun, StrategyConfig
from ragvidence.portable_cli import register_portable_commands
from ragvidence.reporting import build_report
from ragvidence.reporting.html import render_html
from ragvidence.reporting.render import render_report
from ragvidence.runner import run_experiment, write_run
from ragvidence.verification import run_verification
from ragvidence.workspace import create_workspace, restore_workspace

app = typer.Typer(
    name="ragvi",
    help="Diagnose RAG retrieval with evidence-level experiments.",
    no_args_is_help=True,
)
workspace_app = typer.Typer(help="Manage recoverable experiment workspaces.")
app.add_typer(workspace_app, name="workspace")
console = Console()
register_portable_commands(app, console)
DEFAULT_ROOT = Path("workspaces")


def fail(message: str) -> None:
    """Exit with one actionable error and no internal traceback."""
    console.print(f"[red]FAIL[/red] {message}")
    raise typer.Exit(1)


def version_callback(value: bool) -> None:
    if value:
        console.print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback, is_eager=True)
    ] = None,
) -> None:
    """RAGvidence CLI."""


@app.command()
def edition() -> None:
    """Show the CLI license and feature availability."""
    console.print(f"{__edition__} CLI · Apache-2.0 · all included features available")


@app.command()
def health(root: Path = DEFAULT_ROOT) -> None:
    """Check runtime, bundled data, workspace access and semantic support."""
    checks = run_health(root)
    table = Table("Status", "Check", "Detail")
    colors = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}  # nosec B105
    for check in checks:
        table.add_row(f"[{colors[check.status]}]{check.status}[/]", check.name, check.detail)
    console.print(table)
    if any(item.status == "FAIL" for item in checks):
        raise typer.Exit(1)


@app.command()
def verify() -> None:
    """Run deterministic release and installation fixtures."""
    results = run_verification()
    table = Table("Status", "Fixture", "Detail")
    colors = {"PASS": "green", "FAIL": "red"}  # nosec B105
    for result in results:
        table.add_row(
            f"[{colors[result.status]}]{result.status}[/]",
            result.name,
            result.detail,
        )
    console.print(table)
    if any(item.status == "FAIL" for item in results):
        raise typer.Exit(1)


@app.command()
def quickstart(root: Path = DEFAULT_ROOT) -> None:
    """Create the guided exercise without overwriting existing work."""
    try:
        target = create_workspace(root, "heading-context")
    except FileExistsError:
        target = root / "heading-context"
        console.print(f"[yellow]EXISTS[/yellow] {target}")
    console.print(f"[green]READY[/green] {target}\nNext: ragvi validate {target}")


@app.command()
def tutorial(
    root: Path = DEFAULT_ROOT,
    name: Annotated[str, typer.Option(help="Name for the new tutorial workspace")] = "first-run",
) -> None:
    """Run the complete local BM25 tutorial and create a shareable HTML report."""
    try:
        workspace = create_workspace(root, name)
        evaluations = []
        for representation in ("body", "heading_context"):
            config = StrategyConfig(
                name=f"bm25-{representation}",
                strategy="bm25",
                representation=representation,
                k=2,
            )
            console.print(f"Running [cyan]{config.name}[/cyan] at k={config.k}")
            run = run_experiment(workspace, config)
            run_path = workspace / "runs" / f"{config.name}.json"
            write_run(run, run_path)
            sources, questions = load_dataset(workspace)
            evaluation = evaluate_run(run, questions, sources=sources)
            evaluation_path = workspace / "evaluations" / f"{config.name}.json"
            write_json(evaluation_path, evaluation)
            evaluations.append(evaluation)

        report_path = workspace / "reports" / "tutorial.html"
        write_text(report_path, render_report(build_report(evaluations[0], evaluations[1]), "html"))
    except (DatasetError, FileExistsError, OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, FileExistsError):
            fail(
                f"Tutorial workspace already exists: {root / name}. "
                "Inspect it or choose another name with --name."
            )
        fail(str(exc))

    console.print(
        f"[green]COMPLETE[/green] Guided comparison finished.\n"
        f"[bold]Report:[/bold] {report_path}\n"
        f"[bold]Next:[/bold] Open the report, inspect changed questions, then read "
        "the Getting started guide included with your download."
    )


@app.command("init")
def init_workspace(name: str, root: Path = DEFAULT_ROOT) -> None:
    """Create an editable experiment from the bundled template."""
    try:
        target = create_workspace(root, name)
    except (FileExistsError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]CREATED[/green] {target}")


@app.command()
def validate(workspace: Path) -> None:
    """Validate data and evidence-reference integrity."""
    try:
        sources, questions = load_dataset(workspace)
    except DatasetError as exc:
        console.print(f"[red]FAIL[/red] {exc}")
        raise typer.Exit(1) from exc
    evidence = {item for source in sources for item in source.evidence_ids}
    console.print(
        f"[green]PASS[/green] {len(sources)} sources, "
        f"{len(questions)} questions, {len(evidence)} evidence IDs"
    )


@app.command()
def benchmark(
    workspace: Path,
    strategies: str = "bm25",
    k: int = 2,
    model: str = "BAAI/bge-small-en-v1.5",
    provider: str = "fastembed",
) -> None:
    """Run body and heading-context representations."""
    requested = [value.strip() for value in strategies.split(",") if value.strip()]
    unsupported = set(requested) - {"bm25", "semantic", "hybrid"}
    if unsupported:
        raise typer.BadParameter(f"Unsupported strategies: {sorted(unsupported)}")
    if not requested:
        raise typer.BadParameter("Choose at least one retrieval strategy")
    if k < 1:
        raise typer.BadParameter("k must be positive")
    if provider not in {"fastembed", "ollama", "openai_compatible"}:
        raise typer.BadParameter("provider must be fastembed, ollama, or openai_compatible")
    for strategy in requested:
        for representation in ("body", "heading_context"):
            name = f"{strategy}-{representation}"
            config = StrategyConfig(
                name=name,
                strategy=strategy,
                representation=representation,
                k=k,
                model=model if strategy in {"semantic", "hybrid"} else None,
                provider=provider if strategy in {"semantic", "hybrid"} else None,
            )
            if strategy in {"semantic", "hybrid"} and provider != "fastembed":
                console.print(
                    f"[yellow]DISCLOSURE[/yellow] {provider} will receive source text and queries."
                )
            console.print(f"Running [cyan]{name}[/cyan] at k={k}")
            try:
                run = run_experiment(workspace, config)
                destination = workspace / "runs" / f"{name}.json"
                write_run(run, destination)
            except (DatasetError, FileExistsError, RuntimeError) as exc:
                fail(str(exc))
            console.print(f"[green]SAVED[/green] {destination}")


@app.command("import-run")
def import_run(
    workspace: Path,
    input_path: Path,
    name: Annotated[str, typer.Option(help="Stable name for the external strategy")],
    k: Annotated[int, typer.Option(min=1)] = 2,
) -> None:
    """Validate and normalize ranked JSONL from another RAG stack."""
    try:
        run = import_retrieval_run(workspace, input_path, name=name, k=k)
        destination = workspace / "runs" / f"{name}.json"
        write_run(run, destination)
    except (DatasetError, FileExistsError) as exc:
        fail(str(exc))
    console.print(f"[green]SAVED[/green] {destination}")


@app.command()
def experiment(workspace: Path, config_file: Path) -> None:
    """Run one reproducible retrieval pipeline from a JSON configuration."""
    from ragvidence.config import Settings

    try:
        config = StrategyConfig.model_validate_json(config_file.read_text(encoding="utf-8"))
        if any(
            char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for char in config.name
        ):
            raise ValueError("Experiment name must contain only letters, numbers, - or _")
        destination = workspace / "runs" / f"{config.name}.json"
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite existing run: {destination}")
        if config.strategy in {"semantic", "hybrid"}:
            provider_name = config.provider or Settings().embedding_provider
            if provider_name != "fastembed":
                console.print(
                    f"[yellow]DISCLOSURE[/yellow] {provider_name} will receive "
                    "source text and all search queries, including supplied variants."
                )
        if config.reranker_model:
            console.print("Local reranking may download the selected model on first use.")
        run = run_experiment(workspace, config)
        write_run(run, destination)
    except (OSError, ValueError, RuntimeError) as exc:
        fail(str(exc))
    console.print(f"[green]SAVED[/green] {destination}")


@app.command()
def evaluate(workspace: Path, run_file: Path) -> None:
    """Evaluate a run using reviewed evidence labels."""
    try:
        sources, questions = load_dataset(workspace)
        run = ExperimentRun.model_validate_json(run_file.read_text(encoding="utf-8"))
        result = evaluate_run(run, questions, sources=sources)
    except (DatasetError, OSError, ValueError, NotImplementedError) as exc:
        fail(str(exc) or "Evaluation could not be completed")
    destination = workspace / "evaluations" / f"{run.manifest.config.name}.json"
    try:
        write_json(destination, result)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]SAVED[/green] {destination}")


@app.command()
def generate(workspace: Path, run_file: Path, output: Path) -> None:
    """Generate optional answers with a user-configured provider."""
    from ragvidence.config import Settings

    settings = Settings()
    console.print(
        f"[yellow]DISCLOSURE[/yellow] {settings.generation_provider or 'unconfigured provider'} "
        "will receive each question and its retrieved source text."
    )
    try:
        run = ExperimentRun.model_validate_json(run_file.read_text(encoding="utf-8"))
        result = generate_answers(workspace, run, settings)
    except (OSError, ValueError, RuntimeError) as exc:
        fail(str(exc))
    try:
        write_json(output, result)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]SAVED[/green] {output}")


@app.command()
def compare(baseline: Path, intervention: Path, output: Path) -> None:
    """Compare two evaluated runs and retain all change classes."""
    try:
        result = compare_evaluations(
            json.loads(baseline.read_text()), json.loads(intervention.read_text())
        )
    except (OSError, ValueError, json.JSONDecodeError, NotImplementedError) as exc:
        fail(str(exc) or "Comparison could not be completed")
    try:
        write_json(output, result)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print_json(data=result["summary"])


@app.command()
def diagnose(comparison: Path) -> None:
    """Explain an observable pattern and bounded next step."""
    try:
        result = build_diagnosis(json.loads(comparison.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(str(exc))
    for key, value in result.items():
        console.print(f"[bold]{key.replace('_', ' ').title()}:[/bold] {value}")


@app.command()
def inspect(
    run_file: Path,
    question: Annotated[str, typer.Option("--question", help="Stable question ID")],
) -> None:
    """Inspect ranked evidence for one question."""
    try:
        run = ExperimentRun.model_validate_json(run_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(str(exc))
    query = next((item for item in run.queries if item.question_id == question), None)
    if query is None:
        raise typer.BadParameter(f"Question not found: {question}")
    table = Table("Rank", "Source", "Evidence", "Score", "Preview")
    for hit in query.hits:
        table.add_row(
            str(hit.rank),
            hit.source_unit_id,
            ", ".join(sorted(hit.evidence_ids)) or "—",
            f"{hit.score:.4f}",
            hit.preview,
        )
    console.print(table)


@app.command()
def report(
    baseline: Path,
    output: Path,
    intervention: Annotated[Path | None, typer.Option()] = None,
    format: Annotated[str, typer.Option()] = "markdown",
    template: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Create JSON, Markdown or HTML from authoritative evaluation data."""
    if output.exists():
        fail(f"Refusing to overwrite: {output}")
    if format not in {"json", "markdown", "html"}:
        raise typer.BadParameter("format must be json, markdown, or html")
    try:
        baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
        intervention_data = (
            json.loads(intervention.read_text(encoding="utf-8")) if intervention else None
        )
        payload = build_report(baseline_data, intervention_data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(str(exc))
    try:
        if template is not None and format == "html":
            if not template.is_file():
                raise ValueError("The selected HTML report template is missing")
            content = render_html(payload, template)
        else:
            content = render_report(payload, format)
        write_text(output, content)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]SAVED[/green] {output}")


@workspace_app.command("restore")
def workspace_restore(name: str, root: Path = DEFAULT_ROOT) -> None:
    """Back up a workspace and replace it with a clean exercise."""
    try:
        target, backup = restore_workspace(root, name)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]RESTORED[/green] {target}\n[yellow]BACKUP[/yellow] {backup}")
