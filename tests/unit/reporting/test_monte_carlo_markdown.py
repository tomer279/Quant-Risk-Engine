"""Unit tests for Monte Carlo Markdown reporting."""

from __future__ import annotations

from qre.domain.risk import (
    CalibrationWindow,
    MonteCarloRiskResult,
    MonteCarloRunConfig,
    RiskSummary,
)
from qre.reporting import MarkdownMonteCarloReport, MonteCarloReportInput
from qre.validation import ConvergencePoint


def test_render_contains_core_sections() -> None:
    """Rendered memo includes portfolio, seed, analytic VaR, convergence."""
    result = MonteCarloRiskResult(
        portfolio_name="toy",
        notional=1_000_000.0,
        calibration=CalibrationWindow("2020-01-03", "2020-01-10", 5),
        run=MonteCarloRunConfig(2_000, 42, True),
        mc_summary=RiskSummary(0.01, {0.95: 0.02}, {0.95: 0.03}),
        analytic_summary=RiskSummary(0.01, {0.95: 0.021}, {0.95: 0.031}),
    )
    payload = MonteCarloReportInput(
        result=result,
        weights={"AAA": 0.5, "BBB": 0.5},
        convergence=(
            ConvergencePoint(2_000, {0.95: 0.02}, {0.95: 0.03}),
        ),
    )
    text = MarkdownMonteCarloReport().render(payload)
    assert "toy" in text
    assert "seed=42" in text
    assert "AN_VaR=" in text
    assert "Convergence" in text
