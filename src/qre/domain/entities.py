"""Core domain entities for portfolios and datasets.

Exports
-------
Position
    Single-asset portfolio holding.
Portfolio
    Named collection of positions with validated weights.
DatasetRef
    Pointer to a persisted market dataset.
"""

from __future__ import annotations

from dataclasses import dataclass

from qre.domain.errors import PortfolioError
from qre.domain.value_objects import Symbol, Weights


@dataclass(frozen=True, slots=True)
class Position:
    """Single-asset holding inside a portfolio.

    Parameters
    ----------
    symbol : Symbol
        Asset ticker.
    weight : float
        Portfolio weight (validated by ``Portfolio`` / ``Weights``).

    Methods
    -------
    is_long()
        Return whether the weight is strictly positive.
    notional(total)
        Return dollar (or unit) exposure for a total book size.
    """

    symbol: Symbol
    weight: float

    def is_long(self) -> bool:
        """Return whether this position has positive weight.

        Returns
        -------
        bool
            True when ``weight > 0``.
        """
        return self.weight > 0.0

    def notional(self, total: float) -> float:
        """Convert weight to notional exposure.

        Parameters
        ----------
        total : float
            Total portfolio notional.

        Returns
        -------
        float
            ``weight * total``.
        """
        return self.weight * total


@dataclass(frozen=True, slots=True)
class Portfolio:
    """Named portfolio with unique symbols and weights summing to one.

    Parameters
    ----------
    name : str
        Human-readable portfolio id.
    positions : tuple of Position
        Holdings. Prefer ``Portfolio.from_weights``.

    Methods
    -------
    from_weights(name, weights)
        Build from a validated ``Weights`` object.
    symbols()
        Return constituent symbols.
    to_weights()
        Return the equivalent ``Weights`` value object.
    """

    name: str
    positions: tuple[Position, ...]

    def __post_init__(self) -> None:
        cleaned = self.name.strip()
        if not cleaned:
            raise PortfolioError("Portfolio name must be non-empty.")
        object.__setattr__(self, "name", cleaned)
        # Reuse Weights validation (sum, signs, duplicates, non-empty).
        self.to_weights()

    @classmethod
    def from_weights(cls, name: str, weights: Weights) -> Portfolio:
        """Construct a portfolio from validated weights.

        Parameters
        ----------
        name : str
            Portfolio name.
        weights : Weights
            Validated weight map.

        Returns
        -------
        Portfolio
            Portfolio with one position per symbol.
        """
        positions = tuple(
            Position(symbol=symbol, weight=weight)
            for symbol, weight in weights.items
        )
        return cls(name=name, positions=positions)

    def symbols(self) -> tuple[Symbol, ...]:
        """Return constituent symbols in position order.

        Returns
        -------
        tuple of Symbol
            Portfolio symbols.
        """
        return tuple(position.symbol for position in self.positions)

    def to_weights(self) -> Weights:
        """Return weights implied by the positions.

        Returns
        -------
        Weights
            Validated weight map.
        """
        raw = {
            position.symbol: position.weight
            for position in self.positions
        }
        return Weights.from_mapping(raw)


@dataclass(frozen=True, slots=True)
class DatasetRef:
    """Reference to a persisted market dataset on disk.

    Parameters
    ----------
    symbol : Symbol
        Instrument the dataset belongs to.
    relative_path : str
        Path relative to the project data root
        (for example ``'raw/SPY/ohlcv.parquet'``).
    content_hash : str or None, default None
        Optional hash of file contents for reproducibility checks.

    Methods
    -------
    has_content_hash()
        Return whether a content hash is present.
    matches_symbol(raw_symbol)
        Return whether this dataset is for ``raw_symbol``.
    """

    symbol: Symbol
    relative_path: str
    content_hash: str | None = None

    def has_content_hash(self) -> bool:
        """Return whether a content hash is present.

        Returns
        -------
        bool
            True when ``content_hash`` is not None.
        """
        return self.content_hash is not None

    def matches_symbol(self, raw_symbol: str) -> bool:
        """Return whether this dataset belongs to a ticker.

        Parameters
        ----------
        raw_symbol : str
            Ticker string to compare.

        Returns
        -------
        bool
            True when ``symbol`` matches ``raw_symbol``.
        """
        return self.symbol.matches(raw_symbol)
