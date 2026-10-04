"""ForgeLens Command-Line Interface (CLI)."""

import asyncio
import sys
import typer
from rich.console import Console
from rich.table import Table

from forgelens.app.service import ApplicationService

app = typer.Typer(help="ForgeLens — AI Dataset & Model Auditor CLI")
dataset_app = typer.Typer(help="Dataset audit commands")
model_app = typer.Typer(help="Model audit commands")
provider_app = typer.Typer(help="Provider & API token commands")
audit_app = typer.Typer(help="Audit history & export commands")

app.add_typer(dataset_app, name="dataset")
app.add_typer(model_app, name="model")
app.add_typer(provider_app, name="provider")
app.add_typer(audit_app, name="audit")

console = Console()
service = ApplicationService()


@dataset_app.command("audit")
def dataset_audit(
    repo_id: str = typer.Argument(..., help="Dataset repository ID (e.g. username/dataset)"),
    profile: str = typer.Option("General Dataset", "--profile", "-p", help="Audit profile name"),
    samples: int = typer.Option(1000, "--samples", "-s", help="Sample size limit"),
    strategy: str = typer.Option("random", "--strategy", help="Sampling strategy (random, uniform, stratified, first_last)"),
    revision: str = typer.Option("main", "--revision", "-r", help="Git revision branch/tag/commit"),
    output: str = typer.Option("json", "--output", "-o", help="Output format: json, markdown, html"),
):
    """Audit a Hugging Face Dataset without downloading large binary files."""
    console.print(f"[bold blue]Starting Dataset Audit for:[/bold blue] {repo_id}")
    try:
        result = asyncio.run(
            service.run_dataset_audit(
                repo_id=repo_id,
                profile_name=profile,
                sample_size=samples,
                strategy=strategy,
                revision=revision,
            )
        )
        report_str = service.export_audit_report(result, format_type=output)
        console.print(report_str)
    except Exception as err:
        console.print(f"[bold red]Dataset Audit Failed:[/bold red] {err}")
        sys.exit(1)


@model_app.command("audit")
def model_audit(
    repo_id: str = typer.Argument(..., help="Model repository ID (e.g. username/model)"),
    profile: str = typer.Option("General Model Audit", "--profile", "-p", help="Audit profile name"),
    revision: str = typer.Option("main", "--revision", "-r", help="Git revision branch/tag/commit"),
    output: str = typer.Option("json", "--output", "-o", help="Output format: json, markdown, html"),
):
    """Audit a Hugging Face Model metadata and card without downloading weight files."""
    console.print(f"[bold blue]Starting Model Audit for:[/bold blue] {repo_id}")
    try:
        result = asyncio.run(
            service.run_model_audit(
                repo_id=repo_id,
                profile_name=profile,
                revision=revision,
            )
        )
        report_str = service.export_audit_report(result, format_type=output)
        console.print(report_str)
    except Exception as err:
        console.print(f"[bold red]Model Audit Failed:[/bold red] {err}")
        sys.exit(1)


@provider_app.command("list")
def provider_list():
    """List configured API providers and tokens."""
    providers = service.list_providers()
    table = Table(title="ForgeLens Configured API Providers")
    table.add_column("Provider Type", style="cyan")
    table.add_column("Default Model", style="magenta")
    table.add_column("Status", style="green")

    for p in providers:
        status = "Enabled" if p.get("is_enabled") else "Disabled"
        table.add_row(p["provider_type"], p.get("default_model") or "N/A", status)

    console.print(table)


@provider_app.command("configure")
def provider_configure(
    provider_type: str = typer.Argument(..., help="Provider type (openai, huggingface)"),
    key: str = typer.Option(..., "--key", "-k", help="API key or token"),
    base_url: str = typer.Option(None, "--base-url", help="Custom base URL"),
    model: str = typer.Option(None, "--model", "-m", help="Default model"),
):
    """Configure API key/token for a provider."""
    service.configure_provider(
        provider_type=provider_type,
        api_key=key,
        base_url=base_url,
        default_model=model,
        is_enabled=True,
    )
    console.print(f"[bold green]Configured provider '{provider_type}' successfully.[/bold green]")


@audit_app.command("list")
def audit_list(limit: int = typer.Option(20, "--limit", "-l", help="Number of recent audits to show")):
    """List recent local audit history records."""
    records = service.list_history(limit=limit)
    table = Table(title="ForgeLens Audit History")
    table.add_column("Audit ID", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Repository", style="blue")
    table.add_column("Status", style="bold green")
    table.add_column("Score", style="magenta")

    for r in records:
        table.add_row(r.audit_id, r.audit_type, r.repo_id, r.final_status, f"{r.weighted_total_score}/100")

    console.print(table)


if __name__ == "__main__":
    app()
