"""Command-line interface for local evidence-level RAG experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from raglab import __version__
from raglab.comparison import compare_evaluations
from raglab.data import DatasetError, load_dataset
from raglab.diagnosis import diagnose as build_diagnosis
from raglab.evaluation.evaluator import evaluate_run
from raglab.generation import generate_answers
from raglab.health import run_health
from raglab.importer import import_retrieval_run
from raglab.models import ExperimentRun, StrategyConfig
from raglab.reporting import build_report, render_markdown
from raglab.reporting.html import render_html
from raglab.runner import run_experiment, write_run
from raglab.verification import run_verification
from raglab.workspace import create_workspace, restore_workspace

app = typer.Typer(
    name="raglab",
    help="Diagnose RAG retrieval with evidence-level experiments.",
    no_args_is_help=True,
)
workspace_app = typer.Typer(help="Manage recoverable experiment workspaces.")
app.add_typer(workspace_app, name="workspace")
console = Console()
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
    """RAG Debugging Lab CLI."""


@app.command()
def health(root: Path = DEFAULT_ROOT) -> None:
    """Check runtime, bundled data, workspace access and semantic support."""
    checks = run_health(root)
    table = Table("Status", "Check", "Detail")
    colors = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}
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
    colors = {"PASS": "green", "BLOCKED": "yellow", "FAIL": "red"}
    for result in results:
        table.add_row(
            f"[{colors[result.status]}]{result.status}[/]",
            result.name,
            result.detail,
        )
    console.print(table)
    if any(item.status == "FAIL" for item in results):
        raise typer.Exit(1)
    if any(item.status == "BLOCKED" for item in results):
        raise typer.Exit(2)


@app.command()
def quickstart(root: Path = DEFAULT_ROOT) -> None:
    """Create the guided exercise without overwriting existing work."""
    try:
        target = create_workspace(root, "heading-context")
    except FileExistsError:
        target = root / "heading-context"
        console.print(f"[yellow]EXISTS[/yellow] {target}")
    console.print(f"[green]READY[/green] {target}\nNext: uv run raglab validate {target}")


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
    unsupported = set(requested) - {"bm25", "semantic"}
    if unsupported:
        raise typer.BadParameter(f"Unsupported strategies: {sorted(unsupported)}")
    for strategy in requested:
        for representation in ("body", "heading_context"):
            name = f"{strategy}-{representation}"
            config = StrategyConfig(
                name=name,
                strategy=strategy,
                representation=representation,
                k=k,
                model=model if strategy == "semantic" else None,
                provider=provider if strategy == "semantic" else None,
            )
            if strategy == "semantic" and provider != "fastembed":
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
def evaluate(workspace: Path, run_file: Path) -> None:
    """Evaluate a run using reviewed evidence labels."""
    try:
        _, questions = load_dataset(workspace)
        run = ExperimentRun.model_validate_json(run_file.read_text(encoding="utf-8"))
        result = evaluate_run(run, questions)
    except (DatasetError, OSError, ValueError, NotImplementedError) as exc:
        fail(str(exc) or "Evaluation metrics are not installed yet")
    destination = workspace / "evaluations" / f"{run.manifest.config.name}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite: {destination}")
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    console.print(f"[green]SAVED[/green] {destination}")


@app.command()
def generate(workspace: Path, run_file: Path, output: Path) -> None:
    """Generate optional answers with a user-configured provider."""
    from raglab.config import Settings

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
    if output.exists():
        fail(f"Refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    console.print(f"[green]SAVED[/green] {output}")


@app.command()
def compare(baseline: Path, intervention: Path, output: Path) -> None:
    """Compare two evaluated runs and retain all change classes."""
    try:
        result = compare_evaluations(
            json.loads(baseline.read_text()), json.loads(intervention.read_text())
        )
    except (OSError, ValueError, json.JSONDecodeError, NotImplementedError) as exc:
        fail(str(exc) or "Evaluation metrics are not installed yet")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    console.print_json(data=result["summary"])


@app.command()
def diagnose(comparison: Path) -> None:
    """Explain an observable pattern and bounded next step."""
    for key, value in build_diagnosis(json.loads(comparison.read_text())).items():
        console.print(f"[bold]{key.replace('_', ' ').title()}:[/bold] {value}")


@app.command()
def inspect(
    run_file: Path,
    question: Annotated[str, typer.Option("--question", help="Stable question ID")],
) -> None:
    """Inspect ranked evidence for one question."""
    run = ExperimentRun.model_validate_json(run_file.read_text())
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
        raise FileExistsError(f"Refusing to overwrite: {output}")
    if format not in {"json", "markdown", "html"}:
        raise typer.BadParameter("format must be json, markdown, or html")
    baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
    intervention_data = (
        json.loads(intervention.read_text(encoding="utf-8")) if intervention else None
    )
    payload = build_report(baseline_data, intervention_data)
    if format == "json":
        content = json.dumps(payload, indent=2)
    elif format == "markdown":
        content = render_markdown(payload)
    else:
        selected = template or Path(__file__).parent / "reporting/templates/report.html.j2"
        if not selected.is_file():
            raise typer.BadParameter(
                "HTML template is not installed yet. Add the owner contribution at "
                "src/raglab/reporting/templates/report.html.j2"
            )
        content = render_html(payload, selected)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    console.print(f"[green]SAVED[/green] {output}")


@workspace_app.command("restore")
def workspace_restore(name: str, root: Path = DEFAULT_ROOT) -> None:
    """Back up a workspace and replace it with a clean exercise."""
    try:
        target, backup = restore_workspace(root, name)
    except (OSError, ValueError) as exc:
        fail(str(exc))
    console.print(f"[green]RESTORED[/green] {target}\n[yellow]BACKUP[/yellow] {backup}")
