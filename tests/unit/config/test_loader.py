"""Unit tests for YAML config loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from qre.config import default_config_path, load_config
from qre.domain.errors import ConfigError


def test_load_default_config() -> None:
    """Load the checked-in default YAML successfully."""
    config = load_config()
    assert "SPY" in config.universe.symbols
    assert config.paths.raw_dir == "data/raw"
    assert config.logging.level == "INFO"
    assert config.date_range.end is None


def test_default_config_path_exists() -> None:
    """Default config path should point at a real file."""
    path = default_config_path()
    assert path.is_file()


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Missing files raise ConfigError."""
    missing = tmp_path / "nope.yaml"
    with pytest.raises(ConfigError, match="not found"):
        load_config(missing)


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """Schema failures raise ConfigError."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("date_range:\n  start: not-a-date\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid config"):
        load_config(bad)
