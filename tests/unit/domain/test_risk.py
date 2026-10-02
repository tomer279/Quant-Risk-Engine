"""Unit tests for risk result value types."""

from __future__ import annotations

from qre.domain.risk import HistoricalRiskResult, RiskSummary


def test_risk_summary_as_dict() -> None:
    summary = RiskSummary(
        mean_loss=0.01,
        var_by_alpha={0.95: 0.02},
        es_by_alpha={0.95: 0.03},
    )
    payload = summary.as_dict()
    assert payload["mean_loss"] == 0.01
    assert payload["var_by_alpha"]["0.95"] == 0.02


def test_historical_result_format_var_line() -> None:
    summary = RiskSummary(
        mean_loss=0.01,
        var_by_alpha={0.95: 0.02},
        es_by_alpha={0.95: 0.03},
    )
    result = HistoricalRiskResult(
        portfolio_name="demo",
        n_obs=10,
        start_date="2020-01-03",
        end_date="2020-01-16",
        notional=1_000_000.0,
        summary=summary,
    )
    line = result.format_var_line(0.95)
    assert "VaR=0.020000" in line
    assert "ES=0.030000" in line
