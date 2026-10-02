"""Unit tests for historical episode return filtering."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from qre.domain.errors import DataValidationError
from qre.domain.value_objects import DateRange
from qre.scenarios.historical_episode import filter_returns_by_episode


def _synthetic_returns() -> pd.DataFrame:
    index = pd.to_datetime(
        ["2020-02-10", "2020-02-20", "2020-03-01", "2020-04-20"]
    )
    return pd.DataFrame(
        {
            "SPY": [-0.01, -0.02, -0.03, 0.01],
            "TLT": [0.01, 0.02, 0.00, -0.01],
        },
        index=index,
    )


def test_filter_keeps_expected_rows() -> None:
    """Inclusive window keeps only dates inside the episode."""
    returns = _synthetic_returns()
    window = DateRange(start=date(2020, 2, 15), end=date(2020, 4, 15))
    filtered = filter_returns_by_episode(returns, window)
    expected = pd.to_datetime(["2020-02-20", "2020-03-01"])
    assert list(filtered.index) == list(expected)
    assert list(filtered.columns) == ["SPY", "TLT"]


def test_empty_window_raises() -> None:
    """No overlapping dates raises DataValidationError."""
    returns = _synthetic_returns()
    window = DateRange(start=date(2019, 1, 1), end=date(2019, 1, 31))
    with pytest.raises(DataValidationError, match="no return rows"):
        filter_returns_by_episode(returns, window)


def test_non_datetime_index_raises() -> None:
    """Non-datetime index is rejected."""
    returns = pd.DataFrame({"SPY": [0.1, 0.2]})
    window = DateRange(start=date(2020, 1, 1), end=date(2020, 12, 31))
    with pytest.raises(DataValidationError, match="DatetimeIndex"):
        filter_returns_by_episode(returns, window)
