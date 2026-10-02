"""Unit tests for ParquetMarketDataStore."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from qre.domain.errors import PersistenceError
from qre.domain.value_objects import Symbol
from qre.persistence import ParquetMarketDataStore


def _sample_frame() -> pd.DataFrame:
    """Build a tiny OHLCV-like frame for round-trip tests."""
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


def test_save_load_roundtrip(tmp_path: Path) -> None:
    """Saved frames reload identically."""
    store = ParquetMarketDataStore(tmp_path)
    symbol = Symbol("SPY")
    frame = _sample_frame()

    assert not store.exists(symbol)
    store.save(symbol, frame)
    assert store.exists(symbol)

    loaded = store.load(symbol)
    assert_frame_equal(loaded, frame)


def test_load_missing_raises(tmp_path: Path) -> None:
    """Loading a missing symbol raises PersistenceError."""
    store = ParquetMarketDataStore(tmp_path)
    with pytest.raises(PersistenceError, match="No market data"):
        store.load(Symbol("QQQ"))


def test_symbol_path_layout(tmp_path: Path) -> None:
    """Parquet path follows {root}/{SYMBOL}/ohlcv.parquet."""
    store = ParquetMarketDataStore(tmp_path)
    path = store.symbol_path(Symbol("TLT"))
    assert path == tmp_path / "TLT" / "ohlcv.parquet"
