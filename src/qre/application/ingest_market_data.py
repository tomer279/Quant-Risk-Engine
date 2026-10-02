"""Application use-case for market data ingestion.

Exports
-------
IngestDeps
    Source/store pair used by ingest helpers.
ingest_symbol
    Fetch, validate, and persist one symbol.
ingest_universe
    Ingest many symbols with the same window.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from qre.domain.entities import DatasetRef
from qre.domain.protocols import MarketDataSource, MarketDataStore
from qre.domain.value_objects import DateRange, Symbol


@dataclass(frozen=True, slots=True)
class IngestDeps:
    """Dependencies required to ingest market data.

    Parameters
    ----------
    source : MarketDataSource
        External market data adapter.
    store : MarketDataStore
        Local persistence backend.

    Methods
    -------
    source_name()
        Return the upstream source identifier.
    """

    source: MarketDataSource
    store: MarketDataStore

    def source_name(self) -> str:
        """Return the upstream source identifier.

        Returns
        -------
        str
            Value of ``source.source_name()``.
        """
        return self.source.source_name()


def ingest_symbol(
        deps: IngestDeps,
        symbol: Symbol,
        date_range: DateRange,
) -> DatasetRef:
    """Fetch, validate, and persist daily OHLCV for one symbol.

    Parameters
    ----------
    deps : IngestDeps
        Source and store dependencies.
    symbol : Symbol
        Instrument to ingest.
    date_range : DateRange
        Inclusive fetch window.

    Returns
    -------
    DatasetRef
        Pointer to the persisted dataset under the store root.
    """
    frame = deps.source.fetch(symbol, date_range)
    deps.store.save(symbol, frame)
    relative_path = f"{symbol.as_path_key()}/ohlcv.parquet"
    return DatasetRef(symbol=symbol, relative_path=relative_path)


def ingest_universe(
        deps: IngestDeps,
        symbols: Sequence[Symbol],
        date_range: DateRange,
) -> list[DatasetRef]:
    """Ingest each symbol in ``symbols`` over the same date range.

    Parameters
    ----------
    deps : IngestDeps
        Source and store dependencies.
    symbols : sequence of Symbol
        Instruments to ingest.
    date_range : DateRange
        Inclusive fetch window.

    Returns
    -------
    list of DatasetRef
        One reference per successfully ingested symbol, in input order.
    """
    return [
        ingest_symbol(deps, symbol, date_range)
        for symbol in symbols
    ]
