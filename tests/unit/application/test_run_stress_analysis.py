"""Network-free tests for run_stress_analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from qre.application.load_portfolio import PortfolioSpec
from qre.application.run_historical_analysis import AnalysisDeps
from qre.application.run_stress_analysis import run_stress_analysis
from qre.domain.entities import Portfolio
from qre.domain.scenarios import HypotheticalScenario
from qre.domain.value_objects import Symbol, Weights
from qre.persistence import ParquetMarketDataStore


def _ohlcv(closes: list[float], dates: list[str]) -> pd.DataFrame:
    """Build a minimal OHLCV frame from closes."""
    index = pd.to_datetime(dates)
    n_rows = len(closes)
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1_000_000.0] * n_rows,
        },
        index=index,
    )


def test_run_stress_hypothetical_writes_report(tmp_path: Path) -> None:
    """Hypo shock path writes report.md; contribution total matches loss."""
    raw_dir = tmp_path / "raw"
    artifact_dir = tmp_path / "artifacts"
    store = ParquetMarketDataStore(raw_dir)

    # Enough rows for optional cov path; apply_to_historical=False here.
    dates = [
        "2020-01-02",
        "2020-01-03",
        "2020-01-06",
        "2020-01-07",
        "2020-01-08",
    ]
    store.save(Symbol("SPY"), _ohlcv([100.0, 101.0, 99.0, 98.0, 100.0], dates))

    portfolio = Portfolio.from_weights(
        "spy_only",
        Weights.from_mapping({"SPY": 1.0}),
    )
    spec = PortfolioSpec(portfolio=portfolio, notional=1_000_000.0)
    scenario = HypotheticalScenario(
        name="equity_crash",
        description="unit test",
        asset_shocks={"SPY": -0.20},
        vol_multiplier=1.0,
        correlation_inflation=0.0,
        apply_to_historical=False,
    )
    deps = AnalysisDeps(store=store)

    outcome = run_stress_analysis(
        deps,
        spec,
        scenario,
        alphas=(0.95,),
        artifact_dir=artifact_dir,
    )
    result = outcome.result

    assert result.instantaneous is not None
    assert result.instantaneous.portfolio_loss == pytest.approx(0.20)
    assert result.contributions.total == pytest.approx(0.20)
    assert result.historical is None

    assert outcome.report_path.is_file()
    assert "stress" in outcome.report_path.parts
    text = outcome.report_path.read_text(encoding="utf-8")
    assert "equity_crash" in text
    assert "0.200000" in text


def test_run_stress_with_historical_recolor(tmp_path: Path) -> None:
    """apply_to_historical fills HistoricalRiskResult on the outcome."""
    raw_dir = tmp_path / "raw"
    artifact_dir = tmp_path / "artifacts"
    store = ParquetMarketDataStore(raw_dir)

    dates = [f"2020-01-{day:02d}" for day in range(2, 22)]
    closes = [100.0 + (i % 5) for i in range(len(dates))]
    store.save(Symbol("SPY"), _ohlcv(closes, dates))
    store.save(
        Symbol("TLT"),
        _ohlcv([50.0 + (i % 3) for i in range(len(dates))], dates),
    )

    portfolio = Portfolio.from_weights(
        "spy_tlt",
        Weights.from_mapping({"SPY": 0.6, "TLT": 0.4}),
    )
    spec = PortfolioSpec(portfolio=portfolio, notional=1_000_000.0)
    scenario = HypotheticalScenario(
        name="equity_crash",
        description="unit test",
        asset_shocks={"SPY": -0.20, "TLT": 0.05},
        vol_multiplier=1.5,
        correlation_inflation=0.3,
        apply_to_historical=True,
    )

    outcome = run_stress_analysis(
        AnalysisDeps(store=store),
        spec,
        scenario,
        alphas=(0.95,),
        artifact_dir=artifact_dir,
    )
    assert outcome.result.historical is not None
    assert outcome.result.historical.n_obs >= 2
    assert 0.95 in outcome.result.historical.summary.var_by_alpha
    assert outcome.report_path.is_file()
