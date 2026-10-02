"""Orchestrate historical portfolio risk analysis.

Exports
-------
AnalysisDeps
    Store dependency for historical analysis.
run_historical_analysis
    Build returns, losses, measures, and a Markdown artifact.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from qre.application.load_portfolio import PortfolioSpec
from qre.data.returns import build_aligned_return_matrix
from qre.domain.protocols import MarketDataStore
from qre.domain.risk import HistoricalRiskResult
from qre.domain.value_objects import Symbol
from qre.measures import summarize_losses
from qre.models import HistoricalSimulationModel
from qre.reporting import MarkdownHistoricalReport

REPORT_FILENAME = "report.md"
DEFAULT_ALPHAS: tuple[float, ...] = (0.95, 0.99)


@dataclass(frozen=True, slots=True)
class AnalysisDeps:
    """Dependencies for historical analysis.

    Parameters
    ----------
    store : MarketDataStore
        Local OHLCV store (typically ``data/raw``).

    Methods
    -------
    has_symbol(symbol)
        Return whether the store has data for ``symbol``.
    """

    store: MarketDataStore

    def has_symbol(self, symbol: Symbol) -> bool:
        """Return whether market data exists for ``symbol``."""
        return self.store.exists(symbol)


@dataclass(frozen=True, slots=True)
class HistoricalAnalysisOutcome:
    """Result plus artifact path from a historical run.

    Parameters
    ----------
    result : HistoricalRiskResult
        Computed measures and sample metadata.
    report_path : pathlib.Path
        Path to the written ``report.md``.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot including the report path.
    summary_lines()
        Short CLI-friendly lines for key metrics.
    """

    result: HistoricalRiskResult
    report_path: Path

    def as_dict(self) -> dict[str, object]:
        """Return result dict plus report path string."""
        payload = self.result.as_dict()
        payload["report_path"] = str(self.report_path)
        return payload

    def summary_lines(self) -> list[str]:
        """Return human-readable metric lines for the terminal."""
        result = self.result
        lines = [
            f"portfolio: {result.portfolio_name}",
            f"n_obs: {result.n_obs}",
            f"sample: {result.start_date} -> {result.end_date}",
            f"mean_loss: {result.summary.mean_loss:.6f}",
        ]
        for alpha in result.summary.alphas():
            lines.append(result.format_var_line(alpha))
        lines.append(f"report: {self.report_path}")
        return lines


def run_historical_analysis(
        deps: AnalysisDeps,
        spec: PortfolioSpec,
        alphas: Sequence[float],
        artifact_dir: Path,
) -> HistoricalAnalysisOutcome:
    """Run historical VaR/ES and write a Markdown artifact.

    Parameters
    ----------
    deps : AnalysisDeps
        Market data store.
    spec : PortfolioSpec
        Portfolio and notional.
    alphas : sequence of float
        Confidence levels in ``(0, 1)``.
    artifact_dir : pathlib.Path
        Root for artifacts (a per-run subfolder is created).

    Returns
    -------
    HistoricalRiskResult
        Measures plus sample metadata.
    """
    symbols = spec.portfolio.symbols()
    returns = build_aligned_return_matrix(deps.store, symbols)
    model = HistoricalSimulationModel()
    losses = model.generate_losses(spec.portfolio, returns)
    summary = summarize_losses(losses, alphas)

    result = HistoricalRiskResult(
        portfolio_name=spec.portfolio.name,
        n_obs=int(len(losses)),
        start_date=_iso_date(pd.Timestamp(returns.index.min())),
        end_date=_iso_date(pd.Timestamp(returns.index.max())),
        notional=spec.notional,
        summary=summary,
    )

    run_dir = Path(artifact_dir) / _make_analysis_id(spec.portfolio.name)
    report = MarkdownHistoricalReport()
    report.write(
        result,
        spec.portfolio.to_weights().as_dict(),
        run_dir / REPORT_FILENAME,
    )
    report_path = report.write(
        result,
        spec.portfolio.to_weights().as_dict(),
        run_dir / REPORT_FILENAME,
    )
    return HistoricalAnalysisOutcome(
        result=result,
        report_path=report_path
    )


def _iso_date(timestamp: pd.Timestamp) -> str:
    """Format a pandas timestamp as ``YYYY-MM-DD``."""
    return timestamp.date().isoformat()


def _make_analysis_id(portfolio_name: str) -> str:
    """Build ``{slug}_{UTC timestamp}`` analysis folder name."""
    slug = portfolio_name.strip().lower().replace(" ", "_")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{slug}_{stamp}"
