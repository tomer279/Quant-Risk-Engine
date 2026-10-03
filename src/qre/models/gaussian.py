"""Gaussian return-model calibration.

Exports
-------
GaussianParams
    Calibrated mean, covariance, and symbol order.
GaussianReturnModel
    Fit and store multivariate Gaussian moments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from qre.data.covariance import estimate_moments
from qre.domain.errors import DataValidationError, ModelCalibrationError


@dataclass(frozen=True, slots=True)
class GaussianParams:
    """Calibrated Gaussian moments aligned to symbol order.

    Parameters
    ----------
    mu : numpy.ndarray
        Mean vector, shape ``(n_assets,)``.
    cov : numpy.ndarray
        Covariance matrix, shape ``(n_assets, n_assets)``, PSD.
    symbols : tuple of str
        Column order matching ``mu`` / ``cov``.

    Methods
    -------
    n_assets()
        Number of assets.
    as_dict()
        JSON-friendly snapshot.
    """

    mu: np.ndarray
    cov: np.ndarray
    symbols: tuple[str, ...]

    def n_assets(self) -> int:
        """Return the number of assets.

        Returns
        -------
        int
            Length of ``mu``.
        """
        return int(self.mu.shape[0])

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON.

        Returns
        -------
        dict of str to Any
            Symbols plus nested lists for ``mu`` and ``cov``.
        """
        return {
            "symbols": list(self.symbols),
            "mu": self.mu.tolist(),
            "cov": self.cov.tolist(),
        }


class GaussianReturnModel:
    """Calibrate multivariate Gaussian moments from a return matrix.

    Methods
    -------
    calibrate(return_matrix)
        Fit, store, and return ``GaussianParams``.
    params()
        Return the last calibrated params.
    """

    def __init__(self) -> None:
        self._params: GaussianParams | None = None

    def calibrate(self, return_matrix: pd.DataFrame) -> GaussianParams:
        """Estimate ``(mu, Sigma)`` from an aligned return matrix.

        Parameters
        ----------
        return_matrix : pandas.DataFrame
            Simple returns; columns define symbol order.

        Returns
        -------
        GaussianParams
            Calibrated moments.

        Raises
        ------
        ModelCalibrationError
            If moments cannot be estimated from the input.
        """
        try:
            mu, cov = estimate_moments(return_matrix)
        except DataValidationError as exc:
            raise ModelCalibrationError(str(exc)) from exc

        symbols = tuple(str(column) for column in return_matrix.columns)
        if len(symbols) != mu.shape[0]:
            raise ModelCalibrationError(
                "Symbol count does not match calibrated mean length."
            )

        params = GaussianParams(mu=mu, cov=cov, symbols=symbols)
        self._params = params
        return params

    def params(self) -> GaussianParams:
        """Return the last calibrated parameter set.

        Returns
        -------
        GaussianParams
            Stored calibration.

        Raises
        ------
        ModelCalibrationError
            If ``calibrate`` has not been called.
        """
        if self._params is None:
            raise ModelCalibrationError(
                "GaussianReturnModel has not been calibrated."
            )
        return self._params
