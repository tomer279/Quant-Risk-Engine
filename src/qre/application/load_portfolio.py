"""Load portfolio definitions from YAML files.

Exports
-------
PortfolioSpec
    Portfolio plus optional book notional for reporting.
load_portfolio_yaml
    Parse a portfolio YAML into ``PortfolioSpec``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

from qre.domain.entities import Portfolio
from qre.domain.errors import ConfigError, PortfolioError
from qre.domain.value_objects import Weights

DEFAULT_NOTIONAL = 1.0


class PortfolioSpec:
    """Portfolio definition with reporting notional.

    Parameters
    ----------
    portfolio : Portfolio
        Validated portfolio entity.
    notional : float
        Book size used only for currency scaling in reports (M1 measures
        stay in return/loss units).

    Methods
    -------
    symbols()
        Delegate to ``portfolio.symbols()``.
    as_dict()
        Plain dict suitable for reports / JSON.
    """

    def __init__(self, portfolio: Portfolio, notional: float) -> None:
        """Validate and store portfolio + notional.

        Parameters
        ----------
        portfolio : Portfolio
            Domain portfolio.
        notional : float
            Must be finite and strictly positive.
        """
        if notional <= 0.0 or not _is_finite(notional):
            raise PortfolioError(
                "Portfolio notional must be a finite positive number."
            )
        self.portfolio = portfolio
        self.notional = float(notional)

    def symbols(self):
        """Return portfolio symbols in weight order."""
        return self.portfolio.symbols()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly snapshot.

        Returns
        -------
        dict of str to Any
            Name, notional, and weights.
        """
        return {
            "name": self.portfolio.name,
            "notional": self.notional,
            "weights": self.portfolio.to_weights().as_dict(),
        }


def load_portfolio_yaml(path: Path | str) -> PortfolioSpec:
    """Load a portfolio YAML file into a ``PortfolioSpec``.

    Expected shape::

        name: demo_spy_qqq_tlt_gld
        notional: 1000000
        positions:
          SPY: 0.40
          QQQ: 0.20
          ...

    Parameters
    ----------
    path : pathlib.Path or str
        Path to the portfolio YAML.

    Returns
    -------
    PortfolioSpec
        Validated portfolio and notional.

    Raises
    ------
    ConfigError
        If the file is missing, unreadable, or structurally invalid.
    PortfolioError
        If weights/notional fail domain validation.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Portfolio file not found: {config_path}")

    try:
        raw = _read_mapping(config_path)
    except OSError as exc:
        raise ConfigError(
            f"Could not read portfolio file: {config_path}"
        ) from exc

    name = _require_str(raw, "name")
    positions = _require_positions(raw)
    notional = float(raw.get("notional", DEFAULT_NOTIONAL))

    weights = Weights.from_mapping(positions)
    portfolio = Portfolio.from_weights(name, weights)
    return PortfolioSpec(portfolio=portfolio, notional=notional)


def _read_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ConfigError(f"Portfolio root must be a mapping: {path}")
    return loaded


def _require_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Portfolio field '{key}' must be a non-empty string.")
    return value.strip()


def _require_positions(raw: dict[str, Any]) -> dict[str, float]:
    positions = raw.get("positions")
    if not isinstance(positions, dict) or not positions:
        raise ConfigError("Portfolio 'positions' must be a non-empty mapping.")
    parsed: dict[str, float] = {}
    for ticker, weight in positions.items():
        if not isinstance(ticker, str):
            raise ConfigError("Position keys must be ticker strings.")
        try:
            parsed[ticker] = float(weight)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"Invalid weight for position {ticker!r}."
            ) from exc
    return parsed


def _is_finite(value: float) -> bool:
    return math.isfinite(value)
