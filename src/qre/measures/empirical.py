"""Empirical risk measures on a loss sample.

Exports
-------
QUANTILE_METHOD
    Locked NumPy quantile interpolation method for M1.
mean_loss
    Sample mean of losses.
var
    Empirical Value-at-Risk.
expected_shortfall
    Mean of losses at or above VaR.
exceedance_probability
    Fraction of losses strictly above a threshold.
summarize_losses
    Bundle mean / VaR / ES for several alphas.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from qre.domain.errors import DataValidationError
from qre.domain.risk import RiskSummary

QUANTILE_METHOD = "linear"
ALPHA_LOW = 0.0
ALPHA_HIGH = 1.0


def mean_loss(losses: np.ndarray) -> float:
    """Return the sample mean of losses.

    Parameters
    ----------
    losses : numpy.ndarray
        1-D loss sample ``L = -R_p`` (positive = loss).

    Returns
    -------
    float
        Mean loss.

    Raises
    ------
    DataValidationError
        If the sample is empty.
    """
    sample = _as_loss_sample(losses)
    return float(np.mean(sample))


def var(losses: np.ndarray, alpha: float) -> float:
    """Empirical VaR at level ``alpha``.

    Uses ``numpy.quantile(..., method=QUANTILE_METHOD)``.

    Parameters
    ----------
    losses : numpy.ndarray
        1-D loss sample.
    alpha : float
        Confidence level in ``(0, 1)``.

    Returns
    -------
    float
        Empirical VaR.
    """
    sample = _as_loss_sample(losses)
    _validate_alpha(alpha)
    return float(np.quantile(sample, alpha, method=QUANTILE_METHOD))


def expected_shortfall(losses: np.ndarray, alpha: float) -> float:
    """Expected shortfall: mean of losses at or above VaR.

    Parameters
    ----------
    losses : numpy.ndarray
        1-D loss sample.
    alpha : float
        Confidence level in ``(0, 1)``.

    Returns
    -------
    float
        Mean of ``{L : L >= VaR_alpha}``. If that set is empty
        (degenerate), returns VaR itself.
    """
    sample = _as_loss_sample(losses)
    _validate_alpha(alpha)
    threshold = float(np.quantile(sample, alpha, method=QUANTILE_METHOD))
    tail = sample[sample >= threshold]
    if tail.size == 0:
        return threshold
    return float(np.mean(tail))


def exceedance_probability(losses: np.ndarray, threshold: float) -> float:
    """Fraction of losses strictly above ``threshold``.

    Parameters
    ----------
    losses : numpy.ndarray
        1-D loss sample.
    threshold : float
        Loss threshold ``x``.

    Returns
    -------
    float
        ``#{L > x} / T``.
    """
    sample = _as_loss_sample(losses)
    return float(np.mean(sample > threshold))


def summarize_losses(
        losses: np.ndarray,
        alphas: Sequence[float],
) -> RiskSummary:
    """Compute mean loss, VaR, and ES for each alpha.

    Parameters
    ----------
    losses : numpy.ndarray
        1-D loss sample.
    alphas : sequence of float
        Confidence levels (each in ``(0, 1)``).

    Returns
    -------
    RiskSummary
        Bundled empirical measures.

    Raises
    ------
    DataValidationError
        If ``alphas`` is empty or any alpha is invalid.
    """
    if not alphas:
        raise DataValidationError("At least one alpha is required.")

    sample = _as_loss_sample(losses)
    var_by_alpha: dict[float, float] = {}
    es_by_alpha: dict[float, float] = {}
    for alpha in alphas:
        _validate_alpha(alpha)
        var_by_alpha[alpha] = var(sample, alpha)
        es_by_alpha[alpha] = expected_shortfall(sample, alpha)

    return RiskSummary(
        mean_loss=mean_loss(sample),
        var_by_alpha=var_by_alpha,
        es_by_alpha=es_by_alpha,
    )


def _as_loss_sample(losses: np.ndarray) -> np.ndarray:
    """Validate and flatten a loss array."""
    sample = np.asarray(losses, dtype=float).reshape(-1)
    if sample.size == 0:
        raise DataValidationError("Loss sample must be non-empty.")
    if not np.all(np.isfinite(sample)):
        raise DataValidationError("Loss sample must contain only finite values.")
    return sample


def _validate_alpha(alpha: float) -> None:
    """Require ``0 < alpha < 1``."""
    if not ALPHA_LOW < alpha < ALPHA_HIGH:
        raise DataValidationError(
            f"alpha must satisfy 0 < alpha < 1; got {alpha}."
        )
