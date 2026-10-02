"""Risk result types for historical analysis.

Exports
-------
RiskSummary
    Empirical mean / VaR / ES snapshot for a loss sample.
HistoricalRiskResult
    Full historical analysis payload for reports and CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Empirical risk measures for a loss sample.

    Parameters
    ----------
    mean_loss : float
        Sample mean of losses ``L = -R_p``.
    var_by_alpha : dict of float to float
        VaR at each requested confidence level.
    es_by_alpha : dict of float to float
        Expected shortfall at each requested level.

    Methods
    -------
    alphas()
        Return sorted alpha keys present in the summary.
    as_dict()
        JSON-friendly snapshot.
    """

    mean_loss: float
    var_by_alpha: dict[float, float]
    es_by_alpha: dict[float, float]

    def alphas(self) -> tuple[float, ...]:
        """Return confidence levels in ascending order.

        Returns
        -------
        tuple of float
            Sorted alpha keys from ``var_by_alpha``.
        """
        return tuple(sorted(self.var_by_alpha))

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Mean loss plus VaR/ES maps with stringified alpha keys.
        """
        return {
            "mean_loss": self.mean_loss,
            "var_by_alpha": {
                str(alpha): value
                for alpha, value in sorted(self.var_by_alpha.items())
            },
            "es_by_alpha": {
                str(alpha): value
                for alpha, value in sorted(self.es_by_alpha.items())
            },
        }


@dataclass(frozen=True, slots=True)
class HistoricalRiskResult:
    """Historical simulation risk output for one portfolio window.

    Parameters
    ----------
    portfolio_name : str
        Portfolio identifier.
    n_obs : int
        Number of loss observations.
    start_date : str
        First loss date (ISO).
    end_date : str
        Last loss date (ISO).
    notional : float
        Book notional for report context.
    summary : RiskSummary
        Empirical mean / VaR / ES bundle.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_var_line(alpha)
        One-line VaR/ES string for CLI / Markdown.
    """

    portfolio_name: str
    n_obs: int
    start_date: str
    end_date: str
    notional: float
    summary: RiskSummary

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Full result payload.
        """
        payload = {
            "portfolio_name": self.portfolio_name,
            "n_obs": self.n_obs,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "notional": self.notional,
        }
        payload.update(self.summary.as_dict())
        return payload

    def format_var_line(self, alpha: float) -> str:
        """Format VaR and ES for one confidence level.

        Parameters
        ----------
        alpha : float
            Confidence level previously computed.

        Returns
        -------
        str
            Human-readable VaR/ES line.

        Raises
        ------
        KeyError
            If ``alpha`` was not part of this result.
        """
        var_value = self.summary.var_by_alpha[alpha]
        es_value = self.summary.es_by_alpha[alpha]
        pct = alpha * 100.0
        return (
            f"alpha={pct:.2f}%  "
            f"VaR={var_value:.6f}  ES={es_value:.6f}"
        )
