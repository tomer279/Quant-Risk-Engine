"""Unit tests for portfolio return / loss maps."""

from __future__ import annotations

import numpy as np
import pytest

from qre.domain.errors import DataValidationError
from qre.engine.portfolio_pnl import portfolio_losses, portfolio_returns


def test_portfolio_returns_and_losses_hand_check() -> None:
    """Equal weights: R_p and L match the 2-asset hand check."""
    # Row0: 0.10, -0.10 → R_p=0 → L=0
    # Row1: -0.05, 0.15 → R_p=0.05 → L=-0.05
    paths = np.array(
        [
            [0.10, -0.10],
            [-0.05, 0.15],
        ],
        dtype=float,
    )
    weights = np.array([0.5, 0.5], dtype=float)

    returns = portfolio_returns(paths, weights)
    losses = portfolio_losses(paths, weights)

    np.testing.assert_allclose(returns, np.array([0.0, 0.05]))
    np.testing.assert_allclose(losses, np.array([0.0, -0.05]))


def test_weight_length_mismatch_raises() -> None:
    """Reject weights that do not match the asset axis."""
    paths = np.ones((3, 2), dtype=float)
    with pytest.raises(DataValidationError, match="weights length"):
        portfolio_returns(paths, np.array([1.0]))


def test_empty_paths_raise() -> None:
    """Reject an empty path matrix."""
    paths = np.zeros((0, 2), dtype=float)
    with pytest.raises(DataValidationError, match="non-empty"):
        portfolio_losses(paths, np.array([0.5, 0.5]))
