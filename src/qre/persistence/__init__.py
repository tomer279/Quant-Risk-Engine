"""Local persistence for market data and artifacts.

Exports
-------
ParquetMarketDataStore
    Parquet-backed ``MarketDataStore`` implementation.
"""

from qre.persistence.parquet_store import ParquetMarketDataStore

__all__ = ["ParquetMarketDataStore"]
