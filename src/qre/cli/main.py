"""Command-line interface for the Quant Risk Engine.

Exports
-------
app
    Typer application entrypoint.
"""

from __future__ import annotations

from typing import Annotated

import typer

from qre import __version__
from qre.cli.commands import analyze_command, ingest_command, stress_command
from qre.orchestration import configure_logging

app = typer.Typer(
    name="qre",
    help="Quant Risk Engine",
    no_args_is_help=True,
)
ingest_command(app)
analyze_command(app)
stress_command(app)


@app.callback()
def main(
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            help="Logging level (DEBUG, INFO, WARNING, ERROR).",
        ),
    ] = "INFO",
) -> None:
    """Configure process-wide options for QRE commands."""
    configure_logging(log_level)


@app.command("info")
def info() -> None:
    """Print package version."""
    typer.echo(f"qre {__version__}")


if __name__ == "__main__":
    app()
