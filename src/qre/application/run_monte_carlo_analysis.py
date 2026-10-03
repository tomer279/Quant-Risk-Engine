"""Orchestrate Gaussian Monte Carlo portfolio risk analysis.

Exports
-------
MonteCarloAnalysisOutcome
    Result, report path, and convergence table from one MC run.
run_monte_carlo_analysis
    Calibrate, simulate, compare to analytic VaR/ES, write Markdown.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from qre.application.load_portfolio import PortfolioSpec
from qre.application.run_historical_analysis import AnalysisDeps
from qre.data.returns import build_aligned_return_matrix
from qre.domain.risk import (
    CalibrationWindow,
    MonteCarloRiskResult,
    MonteCarloRunConfig,
    RiskSummary,
)
from qre.engine import GaussianMonteCarloEngine, MonteCarloSpec
from qre.measures import summarize_losses
from qre.models import GaussianReturnModel, HistoricalSimulationModel
from qre.models.gaussian import GaussianParams
from qre.reporting.monte_carlo_markdown import (
    MarkdownMonteCarloReport,
    MonteCarloReportInput,
)
from qre.validation import (
    ConvergencePoint,
    convergence_from_losses,
    gaussian_es,
    gaussian_var,
    portfolio_loss_moments,
)

REPORT_FILENAME = "report.md"
PATH_COUNT_CANDIDATES: tuple[int, ...] = (1_000, 5_000, 20_000)


@dataclass(frozen=True, slots=True)
class MonteCarloAnalysisOutcome:
    """Result plus artifact paths from a Monte Carlo run.

    Parameters
    ----------
    result : MonteCarloRiskResult
        MC and analytic risk payload.
    report_path : pathlib.Path
        Written ``report.md`` path.
    convergence : tuple of ConvergencePoint
        Prefix-based VaR/ES table.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot including the report path.
    summary_lines()
        Short CLI-friendly lines for key metrics.
    """

    result: MonteCarloRiskResult
    report_path: Path
    convergence: tuple[ConvergencePoint, ...]

    def as_dict(self) -> dict[str, object]:
        """Return result dict plus report path and convergence."""
        payload = self.result.as_dict()
        payload["report_path"] = str(self.report_path)
        payload["convergence"] = [
            point.as_dict() for point in self.convergence
        ]
        return payload

    def summary_lines(self) -> list[str]:
        """Return human-readable metric lines for the terminal."""
        result = self.result
        lines = [
            f"portfolio: {result.portfolio_name}",
            f"calibration: {result.calibration.format_span()}",
            f"run: {result.run.format_line()}",
            f"mc_mean_loss: {result.mc_summary.mean_loss:.6f}",
            f"analytic_mean_loss: {result.analytic_summary.mean_loss:.6f}",
        ]
        for alpha in result.mc_summary.alphas():
            lines.append(result.format_comparison_line(alpha))
        lines.append(f"report: {self.report_path}")
        return lines

@dataclass(frozen=True, slots=True)
class _SimulationBundle:
    """Intermediate MC simulation artifacts.

    Parameters
    ----------
    returns : pandas.DataFrame
        Calibration return matrix.
    params : GaussianParams
        Calibrated Gaussian moments.
    weights : numpy.ndarray
        Weights aligned to ``params.symbols``.
    losses : numpy.ndarray
        Simulated portfolio losses.

    Methods
    -------
    n_obs()
        Calibration row count.
    weight_map()
        Not needed — keep only two methods if you add another.
    """

    returns: pd.DataFrame
    params: GaussianParams  # or import GaussianParams at runtime
    weights: np.ndarray
    losses: np.ndarray

    def n_obs(self) -> int:
        """Return the number of calibration observations."""
        return int(len(self.returns))

    def calibration_window(self) -> CalibrationWindow:
        """Build the lookback window from the return index."""
        return CalibrationWindow(
            start_date=_iso_date(pd.Timestamp(self.returns.index.min())),
            end_date=_iso_date(pd.Timestamp(self.returns.index.max())),
            n_obs=self.n_obs(),
        )


def _simulate_bundle(
        deps: AnalysisDeps,
        spec: PortfolioSpec,
        mc_spec: MonteCarloSpec,
) -> _SimulationBundle:
    """Load returns, calibrate, and sample portfolio losses."""
    returns = build_aligned_return_matrix(
        deps.store,
        spec.portfolio.symbols(),
    )
    params = GaussianReturnModel().calibrate(returns)
    weights = HistoricalSimulationModel().weight_vector(
        spec.portfolio,
        params.symbols,
    )
    losses = GaussianMonteCarloEngine().sample_losses(
        params,
        weights,
        mc_spec,
    )
    return _SimulationBundle(
        returns=returns,
        params=params,
        weights=weights,
        losses=losses,
    )


def _build_result(
        spec: PortfolioSpec,
        bundle: _SimulationBundle,
        alphas: Sequence[float],
        mc_spec: MonteCarloSpec,
) -> MonteCarloRiskResult:
    """Assemble the domain result from a simulation bundle."""
    return MonteCarloRiskResult(
        portfolio_name=spec.portfolio.name,
        notional=spec.notional,
        calibration=bundle.calibration_window(),
        run=MonteCarloRunConfig(
            n_paths=mc_spec.n_paths,
            seed=mc_spec.seed,
            antithetic=mc_spec.antithetic,
        ),
        mc_summary=summarize_losses(bundle.losses, alphas),
        analytic_summary=_analytic_summary(
            bundle.params.mu,
            bundle.params.cov,
            bundle.weights,
            alphas,
        ),
    )


def _build_convergence(
        losses: np.ndarray,
        n_paths: int,
        alphas: Sequence[float],
) -> tuple[ConvergencePoint, ...]:
    """Build the prefix convergence table."""
    return convergence_from_losses(
        losses,
        path_counts=_default_path_counts(n_paths),
        alphas=alphas,
    )


def _write_report(
        spec: PortfolioSpec,
        result: MonteCarloRiskResult,
        convergence: tuple[ConvergencePoint, ...],
        artifact_dir: Path,
) -> Path:
    """Write the Markdown artifact and return its path."""
    run_dir = Path(artifact_dir) / _make_analysis_id(spec.portfolio.name)
    payload = MonteCarloReportInput(
        result=result,
        weights=spec.portfolio.to_weights().as_dict(),
        convergence=convergence,
    )
    return MarkdownMonteCarloReport().write(
        payload,
        run_dir / REPORT_FILENAME,
    )

def run_monte_carlo_analysis(
        deps: AnalysisDeps,
        spec: PortfolioSpec,
        alphas: Sequence[float],
        artifact_dir: Path,
        mc_spec: MonteCarloSpec,
) -> MonteCarloAnalysisOutcome:
    """Run Gaussian MC VaR/ES, compare to analytic, write Markdown."""
    mc_spec.validate()
    bundle = _simulate_bundle(deps, spec, mc_spec)
    result = _build_result(spec, bundle, alphas, mc_spec)
    convergence = _build_convergence(bundle.losses, mc_spec.n_paths, alphas)
    report_path = _write_report(spec, result, convergence, artifact_dir)
    return MonteCarloAnalysisOutcome(
        result=result,
        report_path=report_path,
        convergence=convergence,
    )


def _analytic_summary(
        mu,
        cov,
        weights,
        alphas: Sequence[float],
) -> RiskSummary:
    """Build closed-form RiskSummary for portfolio losses."""
    mu_l, sigma_l = portfolio_loss_moments(mu, cov, weights)
    var_by_alpha = {
        float(alpha): gaussian_var(mu_l, sigma_l, float(alpha))
        for alpha in alphas
    }
    es_by_alpha = {
        float(alpha): gaussian_es(mu_l, sigma_l, float(alpha))
        for alpha in alphas
    }
    return RiskSummary(
        mean_loss=mu_l,
        var_by_alpha=var_by_alpha,
        es_by_alpha=es_by_alpha,
    )


def _default_path_counts(n_paths: int) -> tuple[int, ...]:
    """Unique ascending prefix lengths ending at ``n_paths``."""
    counts = [n for n in PATH_COUNT_CANDIDATES if n < n_paths]
    counts.append(n_paths)
    return tuple(sorted(set(counts)))


def _iso_date(timestamp: pd.Timestamp) -> str:
    """Format a pandas timestamp as ``YYYY-MM-DD``."""
    return timestamp.date().isoformat()


def _make_analysis_id(portfolio_name: str) -> str:
    """Build ``{slug}_{UTC timestamp}`` analysis folder name."""
    slug = portfolio_name.strip().lower().replace(" ", "_")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{slug}_{stamp}"
