"""Pydantic settings schema for QRE configuration.

Exports
-------
DateRangeConfig
    Inclusive request window from YAML.
PathsConfig
    Local data and artifact directories.
UniverseConfig
    Symbols included in default ingest/analysis.
LoggingConfig
    Process logging settings.
AppConfig
    Top-level application configuration.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DateRangeConfig(BaseModel):
    """Inclusive calendar window for data requests.

    Parameters
    ----------
    start : datetime.date
        First day of the sample.
    end : datetime.date or None, default None
        Last day of the sample. ``None`` means open-ended.
    """

    start: date
    end: date | None = None


class PathsConfig(BaseModel):
    """Filesystem locations for data and artifacts.

    Parameters
    ----------
    raw_dir : str
        Directory for raw vendor extracts.
    processed_dir : str
        Directory for normalized tables.
    artifacts_dir : str
        Directory for analysis outputs.
    """

    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    artifacts_dir: str = "data/artifacts"


class UniverseConfig(BaseModel):
    """Default instrument universe.

    Parameters
    ----------
    symbols : list of str
        Tickers to ingest or analyze when none are passed on the CLI.
    """

    symbols: list[str] = Field(default_factory=lambda: ["SPY"])


class LoggingConfig(BaseModel):
    """Logging settings for CLI and pipelines.

    Parameters
    ----------
    level : str
        Stdlib logging level name (for example ``'INFO'``).
    """

    level: str = "INFO"


class AppConfig(BaseModel):
    """Top-level Quant Risk Engine application configuration.

    Parameters
    ----------
    universe : UniverseConfig
        Default symbols.
    date_range : DateRangeConfig
        Sample window.
    paths : PathsConfig
        Data directories.
    logging : LoggingConfig
        Logging behavior.
    """

    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    date_range: DateRangeConfig
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
