"""CLI command for Gaussian Monte Carlo portfolio risk.

Exports
-------
monte_carlo_command
    Register the ``qre mc`` command on a Typer app.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

from qre.application import (
    AnalysisDeps,
    load_portfolio_yaml,
)
from qre.application.run_monte_carlo_analysis import (
    run_monte_carlo_analysis,
)
from qre.config import load_config, resolve_project_root
from qre.engine import MonteCarloSpec
from qre.persistence import ParquetMarketDataStore

DEFAULT_PORTFOLIO_REL = Path("configs/portfolios/demo_spy_qqq_tlt_gld.yaml")
DEFAULT_ALPHAS: tuple[float, ...] = (0.95, 0.99)
DEFAULT_N_PATHS = 50_000
DEFAULT_SEED = 42
DEFAULT_ANTITHETIC = True
MONTE_CARLO_SUBDIR = "monte_carlo"


@dataclass(frozen=True, slots=True)
class _ResolvedMcPaths:
    """Resolved raw and artifact directories for ``qre mc``.

    Parameters
    ----------
    raw_dir : pathlib.Path
        Market-data root.
    artifact_dir : pathlib.Path
        Monte Carlo artifact root (includes ``monte_carlo`` subdir).

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    raw_exists()
        Whether ``raw_dir`` exists on disk.
    """

    raw_dir: Path
    artifact_dir: Path

    def as_dict(self) -> dict[str, str]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to str
            Resolved ``raw_dir`` and ``artifact_dir`` path strings.
        """
        return {
            "raw_dir": str(self.raw_dir),
            "artifact_dir": str(self.artifact_dir),
        }

    def raw_exists(self) -> bool:
        """Return whether the resolved raw-data directory exists.

        Returns
        -------
        bool
            True if ``raw_dir`` is an existing directory.
        """
        return self.raw_dir.is_dir()


def _run_mc_command(
        portfolio: Path | None,
        alpha: list[float] | None,
        config_path: Path | None,
        n_paths: int,
        seed: int,
) -> object:  # prefer MonteCarloAnalysisOutcome if exported
    """Resolve CLI inputs and run the Monte Carlo use-case."""
    paths = _resolve_mc_paths(config_path)
    return run_monte_carlo_analysis(
        AnalysisDeps(store=ParquetMarketDataStore(root_dir=paths.raw_dir)),
        load_portfolio_yaml(_resolve_portfolio_path(portfolio)),
        alphas=_resolve_alphas(alpha),
        artifact_dir=paths.artifact_dir,
        mc_spec=MonteCarloSpec(
            n_paths=n_paths,
            seed=seed,
            antithetic=DEFAULT_ANTITHETIC,
        ),
    )


def _resolve_mc_paths(config_path: Path | None) -> _ResolvedMcPaths:
    """Load config and resolve raw / artifact directories."""
    config = load_config(config_path)
    artifact_root = _resolve_under_root(Path(config.paths.artifacts_dir))
    return _ResolvedMcPaths(
        raw_dir=_resolve_under_root(Path(config.paths.raw_dir)),
        artifact_dir=artifact_root / MONTE_CARLO_SUBDIR,
    )


def _resolve_alphas(alpha: list[float] | None) -> tuple[float, ...]:
    """Use CLI alphas or package defaults."""
    if alpha:
        return tuple(alpha)
    return DEFAULT_ALPHAS


def _echo_outcome(outcome: object) -> None:
    """Print completion status and summary lines."""
    typer.echo("Monte Carlo analysis completed.")
    for line in outcome.summary_lines():  # type: ignore[attr-defined]
        typer.echo(line)

def monte_carlo_command(app: typer.Typer) -> None:
    """Register the Monte Carlo analysis command.

    Parameters
    ----------
    app : typer.Typer
        Target CLI app instance.
    """

    @app.command("mc")
    def mc(
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
        n_paths: Annotated[
            int,
            typer.Option(
                "--n-paths",
                help="Number of Monte Carlo paths.",
            ),
        ] = DEFAULT_N_PATHS,
        seed: Annotated[
            int,
            typer.Option(
                "--seed",
                help="RNG seed for reproducibility.",
            ),
        ] = DEFAULT_SEED,
    ) -> None:
        """Run Gaussian MC VaR/ES and write a Markdown artifact."""
        _echo_outcome(
            _run_mc_command(portfolio, alpha, config_path, n_paths, seed)
        )


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
