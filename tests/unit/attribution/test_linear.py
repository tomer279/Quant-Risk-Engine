"""Unit tests for linear P&L contributions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qre.attribution.linear import (
    CONTRIB_HOW_MEAN,
    CONTRIB_HOW_SUM,
    CONTRIB_ROW_TOLERANCE,
    aggregate_contributions,
    contributions_from_returns,
)
from qre.domain.entities import Portfolio
from qre.domain.value_objects import Weights
from qre.models.historical import HistoricalSimulationModel


def test_two_asset_contributions_and_row_sum() -> None:
    """Equal-weight two-asset book: L_i and row sums match losses."""
    weights = Weights.from_mapping({"AAA": 0.5, "BBB": 0.5})
    portfolio = Portfolio.from_weights("two_asset", weights)
    returns = pd.DataFrame(
        {
            "AAA": [0.10, -0.20],
            "BBB": [-0.05, 0.00],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )

    contrib = contributions_from_returns(portfolio, returns)
    # L_AAA = -0.5 * R_AAA ; L_BBB = -0.5 * R_BBB
    assert contrib.loc["2020-01-02", "AAA"] == pytest.approx(-0.05)
    assert contrib.loc["2020-01-02", "BBB"] == pytest.approx(0.025)
    assert contrib.loc["2020-01-03", "AAA"] == pytest.approx(0.10)
    assert contrib.loc["2020-01-03", "BBB"] == pytest.approx(0.0)

    losses = HistoricalSimulationModel().generate_losses(portfolio, returns)
    row_sums = contrib.sum(axis=1).to_numpy(dtype=float)
    assert np.allclose(row_sums, losses, atol=CONTRIB_ROW_TOLERANCE)


def test_aggregate_sum_and_mean() -> None:
    """Sum and mean aggregations produce matching totals."""
    weights = Weights.from_mapping({"SPY": 1.0})
    portfolio = Portfolio.from_weights("spy", weights)
    returns = pd.DataFrame(
        {"SPY": [-0.20, -0.10]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    contrib = contributions_from_returns(portfolio, returns)

    summed = aggregate_contributions(contrib, how=CONTRIB_HOW_SUM)
    assert summed.by_symbol["SPY"] == pytest.approx(0.30)
    assert summed.total == pytest.approx(0.30)

    averaged = aggregate_contributions(contrib, how=CONTRIB_HOW_MEAN)
    assert averaged.by_symbol["SPY"] == pytest.approx(0.15)
    assert averaged.total == pytest.approx(0.15)
