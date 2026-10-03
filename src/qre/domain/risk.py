"""Risk result types for historical and Monte Carlo analysis.

Exports
-------
RiskSummary
    Mean / VaR / ES snapshot for a loss sample.
HistoricalRiskResult
    Full historical analysis payload for reports and CLI.
CalibrationWindow
    Lookback window used for Gaussian calibration.
MonteCarloRunConfig
    Recorded MC path count, seed, and antithetic flag.
MonteCarloRiskResult
    Gaussian MC payload with analytic comparison.
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

@dataclass(frozen=True, slots=True)
class CalibrationWindow:
    """Lookback window used to calibrate the Gaussian model.

    Parameters
    ----------
    start_date : str
        First return date (ISO).
    end_date : str
        Last return date (ISO).
    n_obs : int
        Number of return rows in the lookback.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_span()
        Human-readable ``start → end (N=...)`` line.
    """

    start_date: str
    end_date: str
    n_obs: int

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Lookback dates and observation count.
        """
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "n_obs": self.n_obs,
        }

    def format_span(self) -> str:
        """Format the lookback as a single human-readable line.

        Returns
        -------
        str
            ``YYYY-MM-DD → YYYY-MM-DD (N=...)``.
        """
        return (
            f"{self.start_date} → {self.end_date} "
            f"(N={self.n_obs})"
        )


@dataclass(frozen=True, slots=True)
class MonteCarloRunConfig:
    """Recorded Monte Carlo run knobs for reports and artifacts.

    This is the domain record of an engine ``MonteCarloSpec``. Keep the
    engine type out of ``domain``; map fields in the application layer.

    Parameters
    ----------
    n_paths : int
        Number of simulated loss paths.
    seed : int
        RNG seed used for the draw.
    antithetic : bool
        Whether antithetic variates were used.

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_line()
        Human-readable run summary line.
    """

    n_paths: int
    seed: int
    antithetic: bool

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Path count, seed, and antithetic flag.
        """
        return {
            "n_paths": self.n_paths,
            "seed": self.seed,
            "antithetic": self.antithetic,
        }

    def format_line(self) -> str:
        """Format run knobs as a single human-readable line.

        Returns
        -------
        str
            ``paths=... seed=... antithetic=...``.
        """
        return (
            f"paths={self.n_paths} "
            f"seed={self.seed} "
            f"antithetic={self.antithetic}"
        )


@dataclass(frozen=True, slots=True)
class MonteCarloRiskResult:
    """Gaussian MC risk output with analytic comparison.

    Parameters
    ----------
    portfolio_name : str
        Portfolio identifier.
    notional : float
        Book notional for report context.
    calibration : CalibrationWindow
        Lookback used to estimate ``(mu, Sigma)``.
    run : MonteCarloRunConfig
        Recorded path count, seed, and antithetic flag.
    mc_summary : RiskSummary
        Empirical measures on simulated losses.
    analytic_summary : RiskSummary
        Closed-form Gaussian measures
        (``mean_loss`` should be analytic ``mu_L``).

    Methods
    -------
    as_dict()
        JSON-friendly snapshot.
    format_comparison_line(alpha)
        MC vs analytic VaR/ES one-liner.
    """

    portfolio_name: str
    notional: float
    calibration: CalibrationWindow
    run: MonteCarloRunConfig
    mc_summary: RiskSummary
    analytic_summary: RiskSummary

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Nested calibration, run, MC, and analytic payloads.
        """
        return {
            "portfolio_name": self.portfolio_name,
            "notional": self.notional,
            "calibration": self.calibration.as_dict(),
            "run": self.run.as_dict(),
            "mc_summary": self.mc_summary.as_dict(),
            "analytic_summary": self.analytic_summary.as_dict(),
        }

    def format_comparison_line(self, alpha: float) -> str:
        """Format MC and analytic VaR/ES for one confidence level.

        Parameters
        ----------
        alpha : float
            Confidence level present in both summaries.

        Returns
        -------
        str
            Human-readable comparison line.

        Raises
        ------
        KeyError
            If ``alpha`` is missing from either summary.
        """
        pct = alpha * 100.0
        return (
            f"alpha={pct:.2f}%  "
            f"MC_VaR={self.mc_summary.var_by_alpha[alpha]:.6f}  "
            f"AN_VaR={self.analytic_summary.var_by_alpha[alpha]:.6f}  "
            f"MC_ES={self.mc_summary.es_by_alpha[alpha]:.6f}  "
            f"AN_ES={self.analytic_summary.es_by_alpha[alpha]:.6f}"
        )
