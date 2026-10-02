"""Structural interfaces (protocols) for QRE adapters.

Exports
-------
MarketDataSource
    Fetches market bars for a symbol and date range.
MarketDataStore
    Persists and loads normalized OHLCV tables.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import pandas as pd

from qre.domain.value_objects import DateRange, Symbol


@runtime_checkable
class MarketDataSource(Protocol):
    """Fetches market data from an external vendor.

    Methods
    -------
    fetch(symbol, date_range)
        Download or read bars for the request window.
    source_name()
        Return a stable vendor identifier.
    """

    def fetch(self, symbol: Symbol, date_range: DateRange) -> pd.DataFrame:
        """Fetch OHLCV (or equivalent) bars.

        Parameters
        ----------
        symbol : Symbol
            Instrument to fetch.
        date_range : DateRange
            Inclusive calendar request window.

        Returns
        -------
        pandas.DataFrame
            Normalized market bars indexed by session date.
        """
        raise NotImplementedError


    def source_name(self) -> str:
        """Return a stable vendor identifier.

        Returns
        -------
        str
            For example ``'yfinance'``.
        """
        raise NotImplementedError



@runtime_checkable
class MarketDataStore(Protocol):
    """Persists normalized market data locally.

    Methods
    -------
    save(symbol, frame)
        Write a market table for ``symbol``.
    load(symbol)
        Read a previously saved market table.
    exists(symbol)
        Return whether data for ``symbol`` is present.
    """

    def save(self, symbol: Symbol, frame: pd.DataFrame) -> None:
        """Persist a market data table.

        Parameters
        ----------
        symbol : Symbol
            Instrument key.
        frame : pandas.DataFrame
            Normalized OHLCV table.
        """

    def load(self, symbol: Symbol) -> pd.DataFrame:
        """Load a persisted market data table.

        Parameters
        ----------
        symbol : Symbol
            Instrument key.

        Returns
        -------
        pandas.DataFrame
            Normalized OHLCV table.
        """
        raise NotImplementedError


    def exists(self, symbol: Symbol) -> bool:
        """Return whether data for a symbol exists on disk.

        Parameters
        ----------
        symbol : Symbol
            Instrument key.

        Returns
        -------
        bool
            True when a dataset is available.
        """
        raise NotImplementedError
