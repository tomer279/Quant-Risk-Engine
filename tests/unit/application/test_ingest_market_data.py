"""Unit tests for ingest_market_data use-case."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from qre.application import IngestDeps, ingest_symbol, ingest_universe
from qre.domain.value_objects import DateRange, Symbol
from qre.persistence import ParquetMarketDataStore


class _FakeSource:
    """Minimal MarketDataSource double for tests."""

    def fetch(self, symbol: Symbol, date_range: DateRange) -> pd.DataFrame:
        """Return a tiny valid OHLCV frame."""
        del symbol, date_range
        index = pd.to_datetime(["2020-01-02", "2020-01-03"])
        return pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1_000_000.0, 1_100_000.0],
            },
            index=index,
        )

    def source_name(self) -> str:
        """Return a fake vendor name."""
        return "fake"


def test_ingest_symbol_writes_parquet(tmp_path: Path) -> None:
    """ingest_symbol persists data and returns DatasetRef."""
    store = ParquetMarketDataStore(tmp_path)
    deps = IngestDeps(source=_FakeSource(), store=store)
    symbol = Symbol("SPY")
    date_range = DateRange(
        start=pd.Timestamp("2020-01-02").date(),
        end=pd.Timestamp("2020-01-03").date(),
    )

    ref = ingest_symbol(deps, symbol, date_range)

    assert ref.symbol.value == "SPY"
    assert ref.relative_path == "SPY/ohlcv.parquet"
    assert store.exists(symbol)
    loaded = store.load(symbol)
    assert len(loaded) == 2


def test_ingest_universe_order(tmp_path: Path) -> None:
    """ingest_universe returns one DatasetRef per symbol in order."""
    store = ParquetMarketDataStore(tmp_path)
    deps = IngestDeps(source=_FakeSource(), store=store)
    symbols = (Symbol("SPY"), Symbol("TLT"))
    date_range = DateRange(
        start=pd.Timestamp("2020-01-02").date(),
        end=pd.Timestamp("2020-01-03").date(),
    )

    refs = ingest_universe(deps, symbols, date_range)
    assert [ref.symbol.value for ref in refs] == ["SPY", "TLT"]
    assert store.exists(Symbol("SPY"))
    assert store.exists(Symbol("TLT"))
