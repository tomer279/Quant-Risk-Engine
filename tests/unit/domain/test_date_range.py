"""Unit tests for DateRange value object."""

from __future__ import annotations

from datetime import date

import pytest

from qre.domain.errors import DataValidationError
from qre.domain.value_objects import DateRange


def test_date_range_rejects_inverted_bounds() -> None:
    """Reject start after end."""
    with pytest.raises(DataValidationError, match="on or before"):
        DateRange(start=date(2020, 1, 2), end=date(2020, 1, 1))


def test_date_range_contains_boundaries() -> None:
    """Include both endpoints."""
    window = DateRange(start=date(2020, 1, 1), end=date(2020, 1, 31))
    assert window.contains(date(2020, 1, 1))
    assert window.contains(date(2020, 1, 31))
    assert not window.contains(date(2020, 2, 1))


def test_date_range_to_iso_pair() -> None:
    """Return ISO-formatted inclusive bounds."""
    window = DateRange(start=date(2020, 1, 1), end=date(2020, 1, 31))
    assert window.to_iso_pair() == ("2020-01-01", "2020-01-31")
