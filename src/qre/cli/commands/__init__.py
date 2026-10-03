"""Typer command registration modules.

Exports
-------
ingest_command
    Register ``qre ingest``.
analyze_command
    Register ``qre analyze``.
stress_command
    Register ``qre stress``.
monte_carlo_command
    Register ``qre mc``.
"""

from qre.cli.commands.analyze import analyze_command
from qre.cli.commands.ingest import ingest_command
from qre.cli.commands.monte_carlo import monte_carlo_command
from qre.cli.commands.stress import stress_command

__all__ = [
    "analyze_command",
    "ingest_command",
    "monte_carlo_command",
    "stress_command",
]
