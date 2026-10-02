"""Orchestrate portfolio stress analysis.

Exports
-------
StressAnalysisOutcome
    Stress result plus Markdown artifact path.
run_stress_analysis
    Apply a scenario, measure losses, write a stress report.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from qre.application.load_portfolio import PortfolioSpec
from qre.application.run_historical_analysis import AnalysisDeps
from qre.attribution.linear import (
    CONTRIB_HOW_SUM,
    aggregate_contributions,
    contributions_from_returns,
)
from qre.data.returns import build_aligned_return_matrix
from qre.domain.risk import HistoricalRiskResult
from qre.domain.scenarios import (
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    ScenarioSpec,
    StressAnalysisResult,
)
from qre.measures import summarize_losses
from qre.models import HistoricalSimulationModel
from qre.reporting.stress_markdown import MarkdownStressReport
from qre.scenarios.historical_episode import filter_returns_by_episode
from qre.scenarios.hypothetical import (
    HypoStressParams,
    apply_asset_shocks,
    apply_vol_and_corr_stress,
    recolor_returns,
)

REPORT_FILENAME = "report.md"
STRESS_SUBDIR = "stress"
DEFAULT_ALPHAS: tuple[float, ...] = (0.95, 0.99)


@dataclass(frozen=True, slots=True)
class StressAnalysisOutcome:
    """Result plus artifact path from a stress run.

    Parameters
    ----------
    result : StressAnalysisResult
        Stress payload for reports / CLI.
    report_path : pathlib.Path
        Path to the written ``report.md``.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot including the report path.
    summary_lines()
        Short CLI-friendly lines.
    """

    result: StressAnalysisResult
    report_path: Path

    def as_dict(self) -> dict[str, object]:
        """Return result dict plus report path string."""
        payload = self.result.as_dict()
        payload["report_path"] = str(self.report_path)
        return payload

    def summary_lines(self) -> list[str]:
        """Return human-readable lines for the terminal."""
        result = self.result
        lines = [
            f"portfolio: {result.portfolio_name}",
            f"scenario: {result.scenario_name} ({result.scenario_kind})",
            f"contribution_total: {result.contributions.total:.6f}",
        ]
        if result.instantaneous is not None:
            lines.append(result.instantaneous.format_loss_line())
        if result.historical is not None:
            hist = result.historical
            lines.append(f"hist_n_obs: {hist.n_obs}")
            lines.append(f"hist_mean_loss: {hist.summary.mean_loss:.6f}")
            for alpha in hist.summary.alphas():
                lines.append(hist.format_var_line(alpha))
        lines.append(f"report: {self.report_path}")
        return lines


def run_stress_analysis(
        deps: AnalysisDeps,
        spec: PortfolioSpec,
        scenario: ScenarioSpec,
        alphas: Sequence[float],
        artifact_dir: Path,
) -> StressAnalysisOutcome:
    """Run stress analysis and write a Markdown artifact.

    Steps: load aligned returns; branch on scenario kind; compute
    instantaneous and/or historical stressed measures; write report under
    ``artifact_dir / stress / <analysis_id>/``.

    Parameters
    ----------
    deps : AnalysisDeps
        Market data store.
    spec : PortfolioSpec
        Portfolio and notional.
    scenario : ScenarioSpec
        Episode or hypothetical scenario.
    alphas : sequence of float
        VaR/ES levels for any historical sample.
    artifact_dir : pathlib.Path
        Artifacts root (usually ``data/artifacts``).

    Returns
    -------
    StressAnalysisOutcome
        Result payload and report path.
    """
    symbols = spec.portfolio.symbols()
    returns = build_aligned_return_matrix(deps.store, symbols)

    if isinstance(scenario, HistoricalEpisodeScenario):
        result = _run_episode(spec, scenario, returns, alphas)
    elif isinstance(scenario, HypotheticalScenario):
        result = _run_hypothetical(spec, scenario, returns, alphas)
    else:
        # Defensive: ScenarioSpec is a closed union.
        raise TypeError(f"Unsupported scenario type: {type(scenario)!r}")

    run_dir = (
        Path(artifact_dir)
        / STRESS_SUBDIR
        / _make_analysis_id(spec.portfolio.name, scenario.name)
    )
    report_path = MarkdownStressReport().write(
        result,
        spec.portfolio.to_weights().as_dict(),
        scenario,
        run_dir / REPORT_FILENAME,
    )
    return StressAnalysisOutcome(result=result, report_path=report_path)


def _run_episode(
        spec: PortfolioSpec,
        scenario: HistoricalEpisodeScenario,
        returns: pd.DataFrame,
        alphas: Sequence[float],
) -> StressAnalysisResult:
    windowed = filter_returns_by_episode(returns, scenario.window)
    historical = _historical_result(spec, windowed, alphas)
    contrib_frame = contributions_from_returns(spec.portfolio, windowed)
    contributions = aggregate_contributions(contrib_frame, how=CONTRIB_HOW_SUM)
    return StressAnalysisResult(
        portfolio_name=spec.portfolio.name,
        scenario_name=scenario.name,
        scenario_kind=scenario.kind().value,
        contributions=contributions,
        instantaneous=None,
        historical=historical,
    )


def _run_hypothetical(
        spec: PortfolioSpec,
        scenario: HypotheticalScenario,
        returns: pd.DataFrame,
        alphas: Sequence[float],
) -> StressAnalysisResult:
    instantaneous = apply_asset_shocks(spec.portfolio, scenario.asset_shocks)
    historical = None
    if scenario.apply_to_historical:
        historical = _stressed_historical(spec, scenario, returns, alphas)

    return StressAnalysisResult(
        portfolio_name=spec.portfolio.name,
        scenario_name=scenario.name,
        scenario_kind=scenario.kind().value,
        contributions=instantaneous.contributions,
        instantaneous=instantaneous,
        historical=historical,
    )


def _stressed_historical(
        spec: PortfolioSpec,
        scenario: HypotheticalScenario,
        returns: pd.DataFrame,
        alphas: Sequence[float],
) -> HistoricalRiskResult:
    params = HypoStressParams(
        vol_multiplier=scenario.vol_multiplier,
        correlation_inflation=scenario.correlation_inflation,
    )
    working = returns
    if not params.is_inactive():
        cov_base, cov_stressed = apply_vol_and_corr_stress(returns, params)
        working = recolor_returns(returns, cov_base, cov_stressed)
    return _historical_result(spec, working, alphas)


def _historical_result(
        spec: PortfolioSpec,
        returns: pd.DataFrame,
        alphas: Sequence[float],
) -> HistoricalRiskResult:
    model = HistoricalSimulationModel()
    losses = model.generate_losses(spec.portfolio, returns)
    summary = summarize_losses(losses, alphas)
    return HistoricalRiskResult(
        portfolio_name=spec.portfolio.name,
        n_obs=int(len(losses)),
        start_date=_iso_date(pd.Timestamp(returns.index.min())),
        end_date=_iso_date(pd.Timestamp(returns.index.max())),
        notional=spec.notional,
        summary=summary,
    )


def _iso_date(timestamp: pd.Timestamp) -> str:
    """Format a pandas timestamp as ``YYYY-MM-DD``."""
    return timestamp.date().isoformat()


def _make_analysis_id(portfolio_name: str, scenario_name: str) -> str:
    """Build ``{portfolio}_{scenario}_{UTC timestamp}`` folder name."""
    portfolio_slug = portfolio_name.strip().lower().replace(" ", "_")
    scenario_slug = scenario_name.strip().lower().replace(" ", "_")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{portfolio_slug}_{scenario_slug}_{stamp}"
