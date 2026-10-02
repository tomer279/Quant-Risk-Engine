"""Unit tests for Portfolio entity."""

from __future__ import annotations

from qre.domain.entities import Portfolio
from qre.domain.value_objects import Weights


def test_portfolio_from_weights_roundtrip() -> None:
    """Portfolio symbols and weights round-trip through Weights."""
    weights = Weights.from_mapping(
        {"SPY": 0.4, "QQQ": 0.2, "TLT": 0.25, "GLD": 0.15}
    )
    portfolio = Portfolio.from_weights("demo", weights)
    assert portfolio.name == "demo"
    assert portfolio.to_weights().as_dict() == weights.as_dict()
