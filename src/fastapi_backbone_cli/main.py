"""Command-line interface."""

from typing import Annotated

import typer
from rich.console import Console

from fastapi_backbone_cli import __version__
from fastapi_backbone_cli.generator import DEFAULT_TEMPLATE_REF, generate_project

app = typer.Typer(
    name="fastapi-backbone",
    help="Generate independent FastAPI backend projects from FastApiBackbone.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
console = Console()


@app.command()
def create(
    project_name: Annotated[str, typer.Argument(help="New project name, e.g. inventory-api.")],
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Parent output directory."),
    ] = None,
    template_ref: Annotated[
        str, typer.Option("--template-ref", help="FastApiBackbone branch, tag, or commit SHA.")
    ] = DEFAULT_TEMPLATE_REF,
    docker: Annotated[
        bool, typer.Option("--docker/--no-docker", help="Include Docker assets.")
    ] = True,
    kubernetes: Annotated[
        bool, typer.Option("--kubernetes/--no-kubernetes", help="Include Kubernetes assets.")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", help="Allow an existing empty destination directory.")
    ] = False,
) -> None:
    """Create a project from a pinned FastApiBackbone source snapshot."""
    try:
        destination = generate_project(
            project_name=project_name,
            output=output,
            template_ref=template_ref,
            include_docker=docker,
            include_kubernetes=kubernetes,
            force=force,
        )
    except (ValueError, FileExistsError, OSError, RuntimeError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Created[/green] {project_name} at {destination}")
    console.print("\nNext steps:")
    console.print(f"  cd {destination}")
    console.print("  uv sync --extra dev")
    console.print("  cp .env.example .env")
    console.print("  make run")


@app.command()
def features() -> None:
    """List the features available in this generator release."""
    console.print("Included: FastAPI, Pydantic Settings, SQLAlchemy 2.x, Alembic,")
    console.print("JWT/password-authentication primitives, health checks, logging and tests.")
    console.print("Optional: Docker (default on), Kubernetes/Kustomize (default off).")


@app.command()
def version() -> None:
    """Print CLI and default template versions."""
    console.print(f"fastapi-backbone {__version__}")
    console.print(f"template: safuh/FastApiBackbone@{DEFAULT_TEMPLATE_REF}")


if __name__ == "__main__":
    app()
