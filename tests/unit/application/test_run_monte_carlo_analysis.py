"""Network-free tests for run_monte_carlo_analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qre.application import AnalysisDeps, run_monte_carlo_analysis
from qre.application.load_portfolio import PortfolioSpec
from qre.domain.entities import Portfolio
from qre.domain.value_objects import Symbol, Weights
from qre.engine import MonteCarloSpec
from qre.persistence import ParquetMarketDataStore


def _ohlcv(closes: list[float], dates: list[str]) -> pd.DataFrame:
    index = pd.to_datetime(dates)
    n = len(closes)
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1_000_000.0] * n,
        },
        index=index,
    )


def test_run_monte_carlo_analysis_writes_report(tmp_path: Path) -> None:
    """End-to-end MC path writes report.md and returns MC/analytic measures."""
    raw_dir = tmp_path / "raw"
    artifact_dir = tmp_path / "artifacts"
    store = ParquetMarketDataStore(raw_dir)

    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
        "2020-01-09",
    ]
    store.save(Symbol("AAA"), _ohlcv([100, 101, 100, 102, 101, 103], dates))
    store.save(Symbol("BBB"), _ohlcv([200, 198, 199, 197, 198, 196], dates))

    portfolio = Portfolio.from_weights(
        "toy_50_50",
        Weights.from_mapping({"AAA": 0.5, "BBB": 0.5}),
    )
    spec = PortfolioSpec(portfolio=portfolio, notional=1_000_000.0)
    deps = AnalysisDeps(store=store)
    mc_spec = MonteCarloSpec(n_paths=2_000, seed=123, antithetic=True)

    outcome = run_monte_carlo_analysis(
        deps,
        spec,
        alphas=(0.95,),
        artifact_dir=artifact_dir,
        mc_spec=mc_spec,
    )
    result = outcome.result

    assert result.portfolio_name == "toy_50_50"
    assert result.run.n_paths == 2_000
    assert result.run.seed == 123
    assert 0.95 in result.mc_summary.var_by_alpha
    assert 0.95 in result.analytic_summary.var_by_alpha
    assert outcome.convergence[-1].n_paths == 2_000
    assert outcome.report_path.is_file()

    text = outcome.report_path.read_text(encoding="utf-8")
    assert "toy_50_50" in text
    assert "AN_VaR=" in text
