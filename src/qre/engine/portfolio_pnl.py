"""Portfolio return and loss maps from asset return paths.

Exports
-------
portfolio_returns
    ``R_p = R @ w`` for each path/row.
portfolio_losses
    ``L = -R_p`` (positive = loss).
"""

from __future__ import annotations

import numpy as np

from qre.domain.errors import DataValidationError

WEIGHT_AXIS = 0


def portfolio_returns(
        return_paths: np.ndarray,
        weights: np.ndarray,
) -> np.ndarray:
    """Compute portfolio returns for each path.

    Parameters
    ----------
    return_paths : numpy.ndarray
        Asset returns with shape ``(n_paths, n_assets)``.
    weights : numpy.ndarray
        Weight vector with shape ``(n_assets,)``.

    Returns
    -------
    numpy.ndarray
        Portfolio returns with shape ``(n_paths,)``.

    Raises
    ------
    DataValidationError
        If shapes are incompatible or values are non-finite.
    """
    paths, weight_vector = _validate_paths_and_weights(
        return_paths,
        weights,
    )
    return paths @ weight_vector


def portfolio_losses(
        return_paths: np.ndarray,
        weights: np.ndarray,
) -> np.ndarray:
    """Compute portfolio losses ``L = -R @ w``.

    Parameters
    ----------
    return_paths : numpy.ndarray
        Asset returns with shape ``(n_paths, n_assets)``.
    weights : numpy.ndarray
        Weight vector with shape ``(n_assets,)``.

    Returns
    -------
    numpy.ndarray
        Losses with shape ``(n_paths,)`` (positive = loss).
    """
    return -portfolio_returns(return_paths, weights)


def _validate_paths_and_weights(
        return_paths: np.ndarray,
        weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate and normalize path / weight arrays."""
    paths = np.asarray(return_paths, dtype=float)
    weight_vector = np.asarray(weights, dtype=float).reshape(-1)

    if paths.ndim != 2:
        raise DataValidationError(
            "return_paths must be 2-D with shape (n_paths, n_assets)."
        )
    if paths.shape[0] == 0:
        raise DataValidationError("return_paths must be non-empty.")
    if weight_vector.ndim != 1 or weight_vector.size == 0:
        raise DataValidationError("weights must be a non-empty 1-D vector.")
    if paths.shape[1] != weight_vector.shape[WEIGHT_AXIS]:
        raise DataValidationError(
            "weights length must match return_paths asset axis."
        )
    if not np.all(np.isfinite(paths)):
        raise DataValidationError("return_paths must be finite.")
    if not np.all(np.isfinite(weight_vector)):
        raise DataValidationError("weights must be finite.")
    return paths, weight_vector
