"""Hypothetical shock and second-moment stress transforms.

Exports
-------
HypoStressParams
    Vol multiplier, correlation inflation, PSD epsilon.
apply_asset_shocks
    Instantaneous shock loss + linear contributions.
estimate_covariance
    Sample covariance of a return matrix (variables in columns).
correlation_from_covariance
    Convert covariance to correlation with unit diagonal.
inflate_correlation
    Blend correlations toward all-ones.
build_covariance
    Rebuild covariance from vols and correlation.
apply_vol_and_corr_stress
    Estimate Σ and build stressed Σ' with PSD projection.
recolor_returns
    Map demeaned returns from Σ to Σ' second moments.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from qre.domain.entities import Portfolio
from qre.domain.errors import DataValidationError
from qre.domain.scenarios import AssetContributions, InstantaneousShockResult
from qre.scenarios.psd import (
    DEFAULT_PSD_EPSILON,
    matrix_inv_sqrt,
    matrix_sqrt,
    nearest_psd,
)

ONES_CORRELATION_TARGET = 1.0
MIN_COVARIANCE_ROWS = 2
VOL_FLOOR = 0.0


@dataclass(frozen=True, slots=True)
class HypoStressParams:
    """Parameters for vol/correlation stress on a return sample.

    Parameters
    ----------
    vol_multiplier : float
        ``m > 0``; ``1.0`` leaves vols unchanged.
    correlation_inflation : float
        ``lambda`` in ``[0, 1]``.
    psd_epsilon : float
        Eigenvalue floor for PSD projection.

    Methods
    -------
    is_inactive()
        True when vol and corr stress are both off.
    as_dict()
        JSON-friendly snapshot.
    """

    vol_multiplier: float = 1.0
    correlation_inflation: float = 0.0
    psd_epsilon: float = DEFAULT_PSD_EPSILON

    def is_inactive(self) -> bool:
        """Return True if this params object leaves Σ unchanged."""
        return (
            self.vol_multiplier == 1.0
            and self.correlation_inflation == 0.0
        )

    def as_dict(self) -> dict[str, Any]:
        """Return plain parameter dict."""
        return {
            "vol_multiplier": self.vol_multiplier,
            "correlation_inflation": self.correlation_inflation,
            "psd_epsilon": self.psd_epsilon,
        }


def apply_asset_shocks(
        portfolio: Portfolio,
        shocks: Mapping[str, float],
) -> InstantaneousShockResult:
    """Apply instantaneous simple-return shocks to a portfolio.

    Missing portfolio tickers in ``shocks`` are treated as 0.
    Tickers present in ``shocks`` but not in the portfolio raise.

    Parameters
    ----------
    portfolio : Portfolio
        Validated weights.
    shocks : mapping of str to float
        Simple-return shocks (tickers compared uppercased).

    Returns
    -------
    InstantaneousShockResult
        Portfolio loss and per-asset linear contributions.

    Raises
    ------
    DataValidationError
        If any shock ticker is outside the portfolio.
    """
    weights = portfolio.to_weights().as_dict()
    normalized = {
        key.strip().upper(): float(value)
        for key, value in shocks.items()
    }
    extra = sorted(set(normalized) - set(weights))
    if extra:
        raise DataValidationError(
            f"Shock tickers not in portfolio: {extra}."
        )

    by_symbol: dict[str, float] = {}
    for symbol, weight in weights.items():
        shock = normalized.get(symbol, 0.0)
        by_symbol[symbol] = -weight * shock

    total = float(sum(by_symbol.values()))
    contributions = AssetContributions(by_symbol=by_symbol, total=total)
    return InstantaneousShockResult(
        portfolio_loss=total,
        contributions=contributions,
    )


def estimate_covariance(returns: pd.DataFrame) -> np.ndarray:
    """Sample covariance with variables in columns.

    Parameters
    ----------
    returns : pandas.DataFrame
        Simple returns (T x N).

    Returns
    -------
    numpy.ndarray
        ``(N, N)`` sample covariance.

    Raises
    ------
    DataValidationError
        If fewer than ``MIN_COVARIANCE_ROWS`` rows.
    """
    if len(returns) < MIN_COVARIANCE_ROWS:
        raise DataValidationError(
            "Need at least "
            f"{MIN_COVARIANCE_ROWS} return rows to estimate covariance."
        )
    values = returns.to_numpy(dtype=float)
    return np.cov(values, rowvar=False)


def correlation_from_covariance(cov: np.ndarray) -> np.ndarray:
    """Build correlation from covariance; force unit diagonal.

    Parameters
    ----------
    cov : numpy.ndarray
        Square covariance matrix.

    Returns
    -------
    numpy.ndarray
        Correlation matrix with ones on the diagonal.

    Raises
    ------
    DataValidationError
        If any variance on the diagonal is non-positive.
    """
    variances = np.diag(cov).astype(float)
    if np.any(variances <= VOL_FLOOR):
        raise DataValidationError(
            "Covariance diagonal must be strictly positive to form "
            "correlations."
        )
    vols = np.sqrt(variances)
    outer = np.outer(vols, vols)
    corr = cov / outer
    np.fill_diagonal(corr, ONES_CORRELATION_TARGET)
    return corr


def inflate_correlation(
        corr: np.ndarray,
        lambda_: float,
) -> np.ndarray:
    """Inflate correlations toward all-ones.

    Uses ``C' = (1 - λ) C + λ 11^T``, then forces the diagonal to 1.

    Parameters
    ----------
    corr : numpy.ndarray
        Square correlation matrix.
    lambda_ : float
        Inflation weight in ``[0, 1]``.

    Returns
    -------
    numpy.ndarray
        Inflated correlation matrix.

    Raises
    ------
    DataValidationError
        If ``lambda_`` is outside ``[0, 1]``.
    """
    if not 0.0 <= lambda_ <= 1.0 or not np.isfinite(lambda_):
        raise DataValidationError(
            "correlation inflation lambda must be finite and in [0, 1]."
        )
    n_assets = corr.shape[0]
    ones = np.ones((n_assets, n_assets), dtype=float)
    blended = (1.0 - lambda_) * corr + lambda_ * ones
    np.fill_diagonal(blended, ONES_CORRELATION_TARGET)
    return blended


def build_covariance(
        vols: np.ndarray,
        corr: np.ndarray,
) -> np.ndarray:
    """Rebuild covariance from volatilities and correlation.

    Parameters
    ----------
    vols : numpy.ndarray
        1-D asset volatilities.
    corr : numpy.ndarray
        Correlation matrix.

    Returns
    -------
    numpy.ndarray
        ``diag(vols) @ corr @ diag(vols)``.
    """
    scale = np.diag(vols.astype(float))
    return scale @ corr @ scale


def apply_vol_and_corr_stress(
        returns: pd.DataFrame,
        params: HypoStressParams,
) -> tuple[np.ndarray, np.ndarray]:
    """Estimate base Σ and stressed Σ' (PSD-projected).

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical simple returns.
    params : HypoStressParams
        Vol multiplier, correlation inflation, PSD epsilon.

    Returns
    -------
    tuple of numpy.ndarray
        ``(cov_base, cov_stressed)``.
    """
    if params.vol_multiplier <= 0.0 or not np.isfinite(params.vol_multiplier):
        raise DataValidationError("vol_multiplier must be finite and > 0.")

    cov_raw = estimate_covariance(returns)
    cov_base = nearest_psd(cov_raw, epsilon=params.psd_epsilon)
    vols = np.sqrt(np.maximum(np.diag(cov_base), VOL_FLOOR))
    corr = correlation_from_covariance(cov_base)
    corr_stressed = inflate_correlation(corr, params.correlation_inflation)
    vols_stressed = params.vol_multiplier * vols
    cov_stressed_raw = build_covariance(vols_stressed, corr_stressed)
    cov_stressed = nearest_psd(
        cov_stressed_raw,
        epsilon=params.psd_epsilon,
    )
    return cov_base, cov_stressed


def recolor_returns(
        returns: pd.DataFrame,
        cov_base: np.ndarray,
        cov_stressed: np.ndarray,
) -> pd.DataFrame:
    """Recolor demeaned returns to match ``cov_stressed`` second moments.

    Mapping::

        X_c = X - mean(X)
        Y_c = X_c @ Σ_base^{-1/2} @ Σ_stressed^{1/2}
        Y   = Y_c + mean(X)

    Square roots are symmetric PSD roots from ``matrix_sqrt`` /
    ``matrix_inv_sqrt``.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical simple returns (T x N).
    cov_base : numpy.ndarray
        Covariance for the unstressed sample.
    cov_stressed : numpy.ndarray
        Target covariance after vol/corr stress + PSD.

    Returns
    -------
    pandas.DataFrame
        Recolored returns; same index/columns as ``returns``.

    Raises
    ------
    DataValidationError
        If ``returns`` is empty.
    """
    if returns.empty:
        raise DataValidationError("Return matrix must be non-empty.")

    values = returns.to_numpy(dtype=float)
    means = values.mean(axis=0)
    centered = values - means
    inv_sqrt = matrix_inv_sqrt(cov_base)
    sqrt_stressed = matrix_sqrt(cov_stressed)
    recolored = centered @ inv_sqrt @ sqrt_stressed + means
    return pd.DataFrame(
        recolored,
        index=returns.index,
        columns=list(returns.columns),
    )
