"""CLI command for historical portfolio risk analysis.

Exports
-------
analyze_command
    Register the ``qre analyze`` command on a Typer app.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from qre.application import (
    AnalysisDeps,
    load_portfolio_yaml,
    run_historical_analysis,
)
from qre.config import load_config, resolve_project_root
from qre.persistence import ParquetMarketDataStore

DEFAULT_PORTFOLIO_REL = Path("configs/portfolios/demo_spy_qqq_tlt_gld.yaml")
DEFAULT_ALPHAS: tuple[float, ...] = (0.95, 0.99)
HISTORICAL_SUBDIR = "historical"


def analyze_command(app: typer.Typer) -> None:
    """Register the historical analysis command.

    Parameters
    ----------
    app : typer.Typer
        Target CLI app instance.
    """

    @app.command("analyze")
    def analyze(
        portfolio: Annotated[
            Path | None,
            typer.Option(
                "--portfolio",
                help="Path to portfolio YAML (default: demo portfolio).",
            ),
        ] = None,
        alpha: Annotated[
            list[float] | None,
            typer.Option(
                "--alpha",
                help="Confidence level in (0, 1); repeatable.",
            ),
        ] = None,
        config_path: Annotated[
            Path | None,
            typer.Option(
                "--config",
                help="Optional path to a YAML config file.",
            ),
        ] = None,
    ) -> None:
        """Run historical VaR/ES and write a Markdown artifact."""
        config = load_config(config_path)
        portfolio_path = _resolve_portfolio_path(portfolio)
        alphas = tuple(alpha) if alpha else DEFAULT_ALPHAS

        raw_dir = _resolve_under_root(Path(config.paths.raw_dir))
        artifact_root = _resolve_under_root(Path(config.paths.artifacts_dir))
        artifact_dir = artifact_root / HISTORICAL_SUBDIR

        spec = load_portfolio_yaml(portfolio_path)
        deps = AnalysisDeps(store=ParquetMarketDataStore(root_dir=raw_dir))
        outcome = run_historical_analysis(
            deps,
            spec,
            alphas=alphas,
            artifact_dir=artifact_dir,
        )

        typer.echo("Historical analysis completed.")
        for line in outcome.summary_lines():
            typer.echo(line)


def _resolve_portfolio_path(portfolio: Path | None) -> Path:
    """Resolve portfolio YAML against the project root when relative."""
    if portfolio is None:
        path = resolve_project_root() / DEFAULT_PORTFOLIO_REL
    else:
        path = portfolio if portfolio.is_absolute() else (
            resolve_project_root() / portfolio
        )
    if not path.is_file():
        raise typer.BadParameter(f"Portfolio file not found: {path}")
    return path


def _resolve_under_root(path: Path) -> Path:
    """Resolve a config path relative to the project root."""
    if path.is_absolute():
        return path
    return resolve_project_root() / path
