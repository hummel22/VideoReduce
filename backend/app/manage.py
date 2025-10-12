"""Command-line utilities for the backend service."""
from __future__ import annotations

import typer
import uvicorn

from .migrations import run_migrations

app = typer.Typer(help="VideoReduce backend management commands")


@app.command()
def migrate() -> None:
    """Apply all pending database migrations."""

    run_migrations()
    typer.echo("Migrations applied")


@app.command()
def runserver(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI development server with the background worker."""

    uvicorn.run("backend.app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
