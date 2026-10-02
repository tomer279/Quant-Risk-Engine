"""Immutable domain value objects.

Exports
-------
Symbol
    Normalized ticker identifier.
DateRange
    Inclusive calendar date window.
Weights
    Validated portfolio weight map.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from qre.domain.errors import DataValidationError, PortfolioError

WEIGHT_SUM_TOLERANCE = 1e-8
WEIGHT_SUM_TARGET = 1.0


@dataclass(frozen=True, slots=True)
class Symbol:
    """Normalized equity or ETF ticker.

    Parameters
    ----------
    value : str
        Raw ticker string. Stored stripped and uppercased.

    Methods
    -------
    as_path_key()
        Return the ticker form used in storage paths.
    matches(other)
        Return True if ``other`` equals this ticker, ignoring case.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise DataValidationError("Symbol must be a non-empty ticker.")
        object.__setattr__(self, "value", normalized)

    def as_path_key(self) -> str:
        """Return the ticker form used in storage paths.

        Returns
        -------
        str
            Uppercase ticker suitable for directory names.
        """
        return self.value

    def matches(self, other: str) -> bool:
        """Check equality against a raw ticker string.

        Parameters
        ----------
        other : str
            Ticker to compare (case and padding ignored).

        Returns
        -------
        bool
            True if ``other`` refers to the same symbol.
        """
        return self.value == other.strip().upper()


@dataclass(frozen=True, slots=True)
class DateRange:
    """Inclusive calendar date range for data requests.

    Parameters
    ----------
    start : datetime.date
        First day of the range (inclusive).
    end : datetime.date
        Last day of the range (inclusive).

    Methods
    -------
    contains(day)
        Return whether ``day`` lies inside the range.
    to_iso_pair()
        Return ``(start_iso, end_iso)`` strings.

    Raises
    ------
    DataValidationError
        If ``start`` is after ``end``.
    """

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise DataValidationError(
                "DateRange start must be on or before end."
            )

    def contains(self, day: date) -> bool:
        """Return whether a date lies inside the range.

        Parameters
        ----------
        day : datetime.date
            Date to test.

        Returns
        -------
        bool
            True if ``start <= day <= end``.
        """
        return self.start <= day <= self.end

    def to_iso_pair(self) -> tuple[str, str]:
        """Return inclusive bounds as ISO date strings.

        Returns
        -------
        tuple of str
            ``(start.isoformat(), end.isoformat())``.
        """
        return self.start.isoformat(), self.end.isoformat()


@dataclass(frozen=True, slots=True)
class Weights:
    """Validated long-only portfolio weights that sum to one.

    Parameters
    ----------
    items : tuple of (Symbol, float)
        Symbol/weight pairs. Prefer ``Weights.from_mapping``.

    Methods
    -------
    from_mapping(raw)
        Build from a string-or-Symbol mapping.
    symbols()
        Return symbols in stable sorted order.
    as_dict()
        Return a new ``dict`` of symbol value → weight.

    Raises
    ------
    PortfolioError
        If empty, negative/non-finite, duplicate, or sum ≠ 1.
    """

    items: tuple[tuple[Symbol, float], ...]

    def __post_init__(self) -> None:
        if not self.items:
            raise PortfolioError("Weights must contain at least one symbol.")

        seen: set[str] = set()
        total = 0.0
        for symbol, weight in self.items:
            key = symbol.value
            if key in seen:
                raise PortfolioError(
                    f"Duplicate symbol in weights: {key}."
                )
            seen.add(key)
            if not math.isfinite(weight):
                raise PortfolioError(
                    f"Weight for {key} must be finite."
                )
            if weight < 0.0:
                raise PortfolioError(
                    f"Weight for {key} must be non-negative."
                )
            total += weight

        if abs(total - WEIGHT_SUM_TARGET) > WEIGHT_SUM_TOLERANCE:
            raise PortfolioError(
                "Weights must sum to 1.0 within tolerance "
                f"{WEIGHT_SUM_TOLERANCE}; got {total}."
            )

    @classmethod
    def from_mapping(
        cls,
        raw: Mapping[str, float] | Mapping[Symbol, float],
    ) -> Weights:
        """Build weights from a mapping of tickers to weights.

        Parameters
        ----------
        raw : mapping
            Keys are ``Symbol`` or ticker strings; values are weights.

        Returns
        -------
        Weights
            Validated weight object.
        """
        pairs: list[tuple[Symbol, float]] = []
        for key, weight in raw.items():
            symbol = key if isinstance(key, Symbol) else Symbol(key)
            pairs.append((symbol, float(weight)))
        pairs.sort(key=lambda pair: pair[0].value)
        return cls(items=tuple(pairs))

    def symbols(self) -> tuple[Symbol, ...]:
        """Return portfolio symbols in sorted ticker order.

        Returns
        -------
        tuple of Symbol
            Ordered symbols.
        """
        return tuple(symbol for symbol, _ in self.items)

    def as_dict(self) -> dict[str, float]:
        """Return a plain dict of ticker → weight.

        Returns
        -------
        dict of str to float
            Copy of the weight map keyed by ticker string.
        """
        return {symbol.value: weight for symbol, weight in self.items}
