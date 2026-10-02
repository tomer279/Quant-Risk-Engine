"""Unit tests for portfolio YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from qre.application.load_portfolio import load_portfolio_yaml
from qre.domain.errors import ConfigError, PortfolioError


def test_load_demo_portfolio() -> None:
    """Demo YAML loads with sorted weight keys and notional."""
    path = Path("configs/portfolios/demo_spy_qqq_tlt_gld.yaml")
    spec = load_portfolio_yaml(path)
    assert spec.portfolio.name == "demo_spy_qqq_tlt_gld"
    assert spec.notional == pytest.approx(1_000_000.0)
    weights = spec.portfolio.to_weights().as_dict()
    assert weights == {
        "GLD": 0.15,
        "QQQ": 0.20,
        "SPY": 0.40,
        "TLT": 0.25,
    }
    # Symbols follow Weights sort order, not YAML order.
    assert [s.value for s in spec.symbols()] == ["GLD", "QQQ", "SPY", "TLT"]


def test_missing_file_raises(tmp_path: Path) -> None:
    """Missing portfolio path raises ConfigError."""
    with pytest.raises(ConfigError, match="not found"):
        load_portfolio_yaml(tmp_path / "missing.yaml")


def test_bad_weights_raise(tmp_path: Path) -> None:
    """Weights that do not sum to one raise PortfolioError."""
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: bad\npositions:\n  SPY: 0.9\n",
        encoding="utf-8",
    )
    with pytest.raises(PortfolioError, match="sum to 1.0"):
        load_portfolio_yaml(path)


def test_non_positive_notional_raises(tmp_path: Path) -> None:
    """Non-positive notional raises PortfolioError."""
    path = tmp_path / "bad_notional.yaml"
    path.write_text(
        "name: x\nnotional: 0\npositions:\n  SPY: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(PortfolioError, match="notional"):
        load_portfolio_yaml(path)
