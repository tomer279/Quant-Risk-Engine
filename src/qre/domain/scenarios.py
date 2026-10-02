"""Scenario specifications and stress result types.

Exports
-------
HistoricalEpisodeScenario
    Named inclusive date window for episode replay.
HypotheticalScenario
    Asset shocks plus optional vol/corr stress parameters.
ScenarioSpec
    Union alias of the two scenario input types.
AssetContributions
    Linear P&L contributions by symbol.
InstantaneousShockResult
    One-shot shock loss plus contributions.
StressAnalysisResult
    Top-level stress payload for reports and CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qre.domain.enums import ScenarioKind
from qre.domain.risk import HistoricalRiskResult
from qre.domain.value_objects import DateRange

DEFAULT_VOL_MULTIPLIER = 1.0
DEFAULT_CORR_INFLATION = 0.0
DEFAULT_APPLY_TO_HISTORICAL = False


@dataclass(frozen=True, slots=True)
class HistoricalEpisodeScenario:
    """Historical episode: replay returns inside a date window.

    Parameters
    ----------
    name : str
        Scenario id from YAML.
    window : DateRange
        Inclusive start/end for filtering the return matrix.
    description : str
        Human-readable note for reports.

    Methods
    -------
    kind()
        Always ``ScenarioKind.HISTORICAL_EPISODE``.
    as_dict()
        JSON-friendly snapshot.
    """

    name: str
    window: DateRange
    description: str

    def kind(self) -> ScenarioKind:
        """Return the scenario discriminator."""
        return ScenarioKind.HISTORICAL_EPISODE

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON / Markdown."""
        return {
            "name": self.name,
            "kind": self.kind().value,
            "start": self.window.start.isoformat(),
            "end": self.window.end.isoformat(),
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class HypotheticalScenario:
    """Hypothetical stress: shocks and optional second-moment stress.

    Parameters
    ----------
    name : str
        Scenario id from YAML.
    description : str
        Human-readable note for reports.
    asset_shocks : dict of str to float
        Simple-return shocks keyed by ticker (uppercase).
    vol_multiplier : float
        Multiplier ``m > 0`` on asset vols (default 1.0 = off).
    correlation_inflation : float
        ``lambda`` in ``[0, 1]`` toward all-ones correlation.
    apply_to_historical : bool
        If True, also recolor historical returns for VaR/ES (B3+).

    Methods
    -------
    kind()
        Always ``ScenarioKind.HYPOTHETICAL``.
    as_dict()
        JSON-friendly snapshot.
    """

    name: str
    description: str
    asset_shocks: dict[str, float]
    vol_multiplier: float = DEFAULT_VOL_MULTIPLIER
    correlation_inflation: float = DEFAULT_CORR_INFLATION
    apply_to_historical: bool = DEFAULT_APPLY_TO_HISTORICAL

    def kind(self) -> ScenarioKind:
        """Return the scenario discriminator."""
        return ScenarioKind.HYPOTHETICAL

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON / Markdown."""
        return {
            "name": self.name,
            "kind": self.kind().value,
            "description": self.description,
            "asset_shocks": dict(self.asset_shocks),
            "vol_multiplier": self.vol_multiplier,
            "correlation_inflation": self.correlation_inflation,
            "apply_to_historical": self.apply_to_historical,
        }


ScenarioSpec = HistoricalEpisodeScenario | HypotheticalScenario


@dataclass(frozen=True, slots=True)
class AssetContributions:
    """Linear asset contributions ``L_i = -w_i R_i`` (or shock analogue).

    Parameters
    ----------
    by_symbol : dict of str to float
        Contribution per ticker.
    total : float
        Portfolio loss; must equal ``sum(by_symbol.values())`` within tol
        when constructed by attribution helpers (enforced in B2).

    Methods
    -------
    symbols()
        Tickers in sorted order.
    as_dict()
        JSON-friendly snapshot including ``total``.
    """

    by_symbol: dict[str, float]
    total: float

    def symbols(self) -> tuple[str, ...]:
        """Return contribution tickers sorted alphabetically."""
        return tuple(sorted(self.by_symbol))

    def as_dict(self) -> dict[str, Any]:
        """Return contributions and total as a plain dict."""
        return {
            "by_symbol": {
                symbol: self.by_symbol[symbol]
                for symbol in self.symbols()
            },
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class InstantaneousShockResult:
    """Instantaneous hypothetical shock P&L.

    Parameters
    ----------
    portfolio_loss : float
        ``L = -w^T s``.
    contributions : AssetContributions
        Per-asset linear contributions.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_loss_line()
        One-line summary for CLI / Markdown.
    """

    portfolio_loss: float
    contributions: AssetContributions

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON."""
        return {
            "portfolio_loss": self.portfolio_loss,
            "contributions": self.contributions.as_dict(),
        }

    def format_loss_line(self) -> str:
        """Format portfolio shock loss for reports."""
        return f"instantaneous_loss={self.portfolio_loss:.6f}"


@dataclass(frozen=True, slots=True)
class StressAnalysisResult:
    """Stress analysis payload for reports (filled by B4 orchestration).

    Parameters
    ----------
    portfolio_name : str
        Portfolio id.
    scenario_name : str
        Scenario id.
    scenario_kind : str
        ``ScenarioKind`` value string.
    contributions : AssetContributions
        Primary contribution table for the report.
    instantaneous : InstantaneousShockResult or None
        Present for hypothetical asset shocks.
    historical : HistoricalRiskResult or None
        Episode window and/or recolored historical VaR/ES.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_contribution_table()
        Markdown-friendly contribution lines.
    """

    portfolio_name: str
    scenario_name: str
    scenario_kind: str
    contributions: AssetContributions
    instantaneous: InstantaneousShockResult | None
    historical: HistoricalRiskResult | None

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON."""
        return {
            "portfolio_name": self.portfolio_name,
            "scenario_name": self.scenario_name,
            "scenario_kind": self.scenario_kind,
            "contributions": self.contributions.as_dict(),
            "instantaneous": (
                None
                if self.instantaneous is None
                else self.instantaneous.as_dict()
            ),
            "historical": (
                None if self.historical is None else self.historical.as_dict()
            ),
        }

    def format_contribution_table(self) -> str:
        """Return a simple Markdown table of contributions."""
        lines = [
            "| Symbol | Contribution |",
            "|--------|--------------|",
        ]
        for symbol in self.contributions.symbols():
            value = self.contributions.by_symbol[symbol]
            lines.append(f"| {symbol} | {value:.6f} |")
        total = self.contributions.total
        lines.append(f"| TOTAL | {total:.6f} |")
        return "\n".join(lines)
