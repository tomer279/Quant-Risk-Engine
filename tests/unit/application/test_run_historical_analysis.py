"""Network-free tests for run_historical_analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qre.application import AnalysisDeps, run_historical_analysis
from qre.application.load_portfolio import PortfolioSpec
from qre.domain.entities import Portfolio
from qre.domain.value_objects import Symbol, Weights
from qre.persistence import ParquetMarketDataStore


def _ohlcv(closes: list[float], dates: list[str]) -> pd.DataFrame:
    """Build a minimal OHLCV frame from closes."""
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


def test_run_historical_analysis_writes_report(tmp_path: Path) -> None:
    """End-to-end historical path writes report.md and returns measures."""
    raw_dir = tmp_path / "raw"
    artifact_dir = tmp_path / "artifacts"
    store = ParquetMarketDataStore(raw_dir)

    store.save(
        Symbol("AAA"),
        _ohlcv(
            [100.0, 110.0, 100.0],
            ["2020-01-02", "2020-01-03", "2020-01-06"],
        ),
    )
    store.save(
        Symbol("BBB"),
        _ohlcv(
            [200.0, 180.0, 190.0],
            ["2020-01-02", "2020-01-03", "2020-01-06"],
        ),
    )

    portfolio = Portfolio.from_weights(
        "toy_50_50",
        Weights.from_mapping({"AAA": 0.5, "BBB": 0.5}),
    )
    spec = PortfolioSpec(portfolio=portfolio, notional=1_000_000.0)
    deps = AnalysisDeps(store=store)

    outcome = run_historical_analysis(
        deps,
        spec,
        alphas=(0.95,),
        artifact_dir=artifact_dir,
    )
    result = outcome.result

    assert result.portfolio_name == "toy_50_50"
    assert result.n_obs == 2
    assert result.start_date == "2020-01-03"
    assert result.end_date == "2020-01-06"
    assert 0.95 in result.summary.var_by_alpha
    assert 0.95 in result.summary.es_by_alpha

    assert outcome.report_path.is_file()
    text = outcome.report_path.read_text(encoding="utf-8")
    assert "toy_50_50" in text
    assert "VaR=" in text
