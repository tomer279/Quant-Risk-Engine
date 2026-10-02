"""Unit tests for HistoricalSimulationModel.

Hand check (equal weights 0.5 / 0.5)
------------------------------------
Returns row 1: AAA=+0.10, BBB=-0.10 → R_p=0.00 → L=0.00
Returns row 2: AAA=-0.05, BBB=+0.15 → R_p=0.05 → L=-0.05
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qre.domain.entities import Portfolio
from qre.domain.errors import DataValidationError
from qre.domain.value_objects import Weights
from qre.models import HistoricalSimulationModel


def _two_asset_portfolio() -> Portfolio:
    weights = Weights.from_mapping({"AAA": 0.5, "BBB": 0.5})
    return Portfolio.from_weights("toy", weights)


def test_generate_losses_hand_check() -> None:
    """Losses match the 2-asset spreadsheet check above."""
    model = HistoricalSimulationModel()
    portfolio = _two_asset_portfolio()
    returns = pd.DataFrame(
        {
            "AAA": [0.10, -0.05],
            "BBB": [-0.10, 0.15],
        },
        index=pd.to_datetime(["2020-01-03", "2020-01-06"]),
    )

    losses = model.generate_losses(portfolio, returns)
    expected = np.array([0.00, -0.05], dtype=float)
    np.testing.assert_allclose(losses, expected)


def test_column_order_does_not_matter() -> None:
    """Weights follow matrix columns, not portfolio sort alone."""
    model = HistoricalSimulationModel()
    portfolio = _two_asset_portfolio()
    # BBB before AAA — opposite of alphabetical Weights order
    returns = pd.DataFrame(
        {
            "BBB": [-0.10, 0.15],
            "AAA": [0.10, -0.05],
        }
    )
    losses = model.generate_losses(portfolio, returns)
    expected = np.array([0.00, -0.05], dtype=float)
    np.testing.assert_allclose(losses, expected)


def test_mismatched_columns_raise() -> None:
    """Raise when return columns are not the portfolio symbols."""
    model = HistoricalSimulationModel()
    portfolio = _two_asset_portfolio()
    returns = pd.DataFrame({"AAA": [0.1], "CCC": [0.2]})
    with pytest.raises(DataValidationError, match="must match"):
        model.generate_losses(portfolio, returns)


def test_empty_matrix_raises() -> None:
    """Raise when the return matrix has no rows."""
    model = HistoricalSimulationModel()
    portfolio = _two_asset_portfolio()
    returns = pd.DataFrame(columns=["AAA", "BBB"])
    with pytest.raises(DataValidationError, match="non-empty"):
        model.generate_losses(portfolio, returns)
