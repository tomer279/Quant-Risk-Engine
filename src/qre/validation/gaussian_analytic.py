"""Closed-form Gaussian VaR and ES under linear portfolio losses.

Exports
-------
portfolio_loss_moments
    ``(mu_L, sigma_L)`` from ``(mu, cov, weights)``.
gaussian_var
    Analytic VaR at level ``alpha``.
gaussian_es
    Analytic ES at level ``alpha``.
gaussian_var_es
    Pair helper returning ``(VaR, ES)``.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm  # type: ignore

from qre.domain.errors import DataValidationError

ALPHA_LOW = 0.0
ALPHA_HIGH = 1.0
VOL_FLOOR = 0.0


def portfolio_loss_moments(
        mu: np.ndarray,
        cov: np.ndarray,
        weights: np.ndarray,
) -> tuple[float, float]:
    """Return loss mean and volatility for ``L = -w^T R``.

    Parameters
    ----------
    mu : numpy.ndarray
        Asset mean vector ``(n,)``.
    cov : numpy.ndarray
        Asset covariance ``(n, n)``.
    weights : numpy.ndarray
        Portfolio weights ``(n,)``.

    Returns
    -------
    mu_l : float
        Loss mean ``-w^T mu``.
    sigma_l : float
        Loss volatility ``sqrt(w^T cov w)``.
    """
    mean_vec, cov_mat, weight_vec = _validate_moments(mu, cov, weights)
    mu_p = float(weight_vec @ mean_vec)
    var_p = float(weight_vec @ cov_mat @ weight_vec)
    if var_p < VOL_FLOOR or not np.isfinite(var_p):
        raise DataValidationError(
            "Portfolio variance must be finite and non-negative."
        )
    sigma_l = float(np.sqrt(max(var_p, VOL_FLOOR)))
    return -mu_p, sigma_l


def gaussian_var(mu_l: float, sigma_l: float, alpha: float) -> float:
    """Analytic Gaussian VaR on the loss scale.

    Parameters
    ----------
    mu_l : float
        Loss mean.
    sigma_l : float
        Loss volatility (``>= 0``).
    alpha : float
        Confidence level in ``(0, 1)``.

    Returns
    -------
    float
        ``mu_L + sigma_L * Phi^{-1}(alpha)``.
    """
    _validate_alpha(alpha)
    _validate_sigma(sigma_l)
    return float(mu_l + sigma_l * norm.ppf(alpha))


def gaussian_es(mu_l: float, sigma_l: float, alpha: float) -> float:
    """Analytic Gaussian ES on the loss scale.

    Parameters
    ----------
    mu_l : float
        Loss mean.
    sigma_l : float
        Loss volatility (``>= 0``).
    alpha : float
        Confidence level in ``(0, 1)``.

    Returns
    -------
    float
        ``mu_L + sigma_L * phi(z) / (1 - alpha)`` with
        ``z = Phi^{-1}(alpha)``.
    """
    _validate_alpha(alpha)
    _validate_sigma(sigma_l)
    z_alpha = float(norm.ppf(alpha))
    tail_mass = 1.0 - alpha
    return float(mu_l + sigma_l * norm.pdf(z_alpha) / tail_mass)


def gaussian_var_es(
        mu_l: float,
        sigma_l: float,
        alpha: float,
) -> tuple[float, float]:
    """Return analytic ``(VaR, ES)`` for one alpha."""
    return (
        gaussian_var(mu_l, sigma_l, alpha),
        gaussian_es(mu_l, sigma_l, alpha),
    )


def _validate_moments(
        mu: np.ndarray,
        cov: np.ndarray,
        weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean_vec = np.asarray(mu, dtype=float).reshape(-1)
    cov_mat = np.asarray(cov, dtype=float)
    weight_vec = np.asarray(weights, dtype=float).reshape(-1)
    n_assets = mean_vec.shape[0]

    if n_assets == 0:
        raise DataValidationError("mu must be non-empty.")
    if cov_mat.shape != (n_assets, n_assets):
        raise DataValidationError("cov shape must be (n_assets, n_assets).")
    if weight_vec.shape[0] != n_assets:
        raise DataValidationError("weights length must match mu.")
    if not np.all(np.isfinite(mean_vec)):
        raise DataValidationError("mu must be finite.")
    if not np.all(np.isfinite(cov_mat)):
        raise DataValidationError("cov must be finite.")
    if not np.all(np.isfinite(weight_vec)):
        raise DataValidationError("weights must be finite.")
    return mean_vec, cov_mat, weight_vec


def _validate_alpha(alpha: float) -> None:
    if not ALPHA_LOW < alpha < ALPHA_HIGH:
        raise DataValidationError(
            f"alpha must satisfy 0 < alpha < 1; got {alpha}."
        )


def _validate_sigma(sigma_l: float) -> None:
    if sigma_l < VOL_FLOOR or not np.isfinite(sigma_l):
        raise DataValidationError("sigma_l must be finite and >= 0.")
