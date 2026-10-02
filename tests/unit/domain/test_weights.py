"""Unit tests for portfolio weight validation."""

from __future__ import annotations

import pytest

from qre.domain.errors import PortfolioError
from qre.domain.value_objects import Weights


def test_valid_weights_sum_to_one() -> None:
    """Accept weights that sum to one."""
    weights = Weights.from_mapping({"SPY": 0.4, "TLT": 0.6})
    assert weights.as_dict() == {"SPY": 0.4, "TLT": 0.6}


def test_weights_reject_bad_sum() -> None:
    """Reject weights that do not sum to one."""
    with pytest.raises(PortfolioError, match="sum to 1.0"):
        Weights.from_mapping({"SPY": 0.9})


def test_weights_reject_empty() -> None:
    """Reject an empty weight map."""
    with pytest.raises(PortfolioError, match="at least one"):
        Weights.from_mapping({})


def test_weights_reject_negative() -> None:
    """Reject negative weights in the M0 long-only engine."""
    with pytest.raises(PortfolioError, match="non-negative"):
        Weights.from_mapping({"SPY": 1.5, "TLT": -0.5})
