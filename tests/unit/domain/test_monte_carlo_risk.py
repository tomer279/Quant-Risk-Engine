"""Unit tests for Monte Carlo domain result types."""

from __future__ import annotations

from qre.domain.risk import (
    CalibrationWindow,
    MonteCarloRiskResult,
    MonteCarloRunConfig,
    RiskSummary,
)


def _sample_result() -> MonteCarloRiskResult:
    summary_mc = RiskSummary(
        mean_loss=0.01,
        var_by_alpha={0.95: 0.02},
        es_by_alpha={0.95: 0.03},
    )
    summary_an = RiskSummary(
        mean_loss=0.009,
        var_by_alpha={0.95: 0.021},
        es_by_alpha={0.95: 0.031},
    )
    return MonteCarloRiskResult(
        portfolio_name="demo",
        notional=1_000_000.0,
        calibration=CalibrationWindow(
            start_date="2020-01-03",
            end_date="2020-12-31",
            n_obs=250,
        ),
        run=MonteCarloRunConfig(
            n_paths=10_000,
            seed=7,
            antithetic=True,
        ),
        mc_summary=summary_mc,
        analytic_summary=summary_an,
    )


def test_as_dict_nests_calibration_and_run() -> None:
    """as_dict nests calibration, run, and both risk summaries."""
    payload = _sample_result().as_dict()
    assert payload["calibration"]["n_obs"] == 250
    assert payload["run"]["seed"] == 7
    assert payload["mc_summary"]["var_by_alpha"]["0.95"] == 0.02
    assert payload["analytic_summary"]["var_by_alpha"]["0.95"] == 0.021


def test_format_comparison_line() -> None:
    """Comparison line includes MC and analytic VaR values."""
    line = _sample_result().format_comparison_line(0.95)
    assert "MC_VaR=0.020000" in line
    assert "AN_VaR=0.021000" in line
