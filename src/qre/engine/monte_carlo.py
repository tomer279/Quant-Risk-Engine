"""Gaussian Monte Carlo sampling via Cholesky.

Exports
-------
MonteCarloSpec
    Path count, seed, and antithetic flag.
GaussianMonteCarloEngine
    Sample correlated Gaussian returns and portfolio losses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from qre.domain.errors import DataValidationError
from qre.engine.portfolio_pnl import portfolio_losses
from qre.models.gaussian import GaussianParams

MIN_PATHS = 1
PATH_AXIS = 0
ASSET_AXIS = 1


@dataclass(frozen=True, slots=True)
class MonteCarloSpec:
    """Configuration for a seeded Monte Carlo draw.

    Parameters
    ----------
    n_paths : int
        Number of simulated return rows (must be even if antithetic).
    seed : int
        RNG seed for reproducibility.
    antithetic : bool, default False
        If True, pair each ``Z`` with ``-Z``.

    Methods
    -------
    validate()
        Raise if the spec is inconsistent.
    as_dict()
        JSON-friendly snapshot.
    """

    n_paths: int
    seed: int
    antithetic: bool = False

    def validate(self) -> None:
        """Validate path count and antithetic parity.

        Raises
        ------
        DataValidationError
            If ``n_paths`` is invalid for the antithetic setting.
        """
        if self.n_paths < MIN_PATHS:
            raise DataValidationError(
                f"n_paths must be >= {MIN_PATHS}; got {self.n_paths}."
            )
        if self.antithetic and self.n_paths % 2 != 0:
            raise DataValidationError(
                "n_paths must be even when antithetic=True."
            )

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON."""
        return {
            "n_paths": self.n_paths,
            "seed": self.seed,
            "antithetic": self.antithetic,
        }


class GaussianMonteCarloEngine:
    """Cholesky sampler for multivariate Gaussian returns.

    Methods
    -------
    sample_returns(params, spec)
        Draw correlated asset return paths.
    sample_losses(params, weights, spec)
        Draw portfolio losses ``L = -R w``.
    """

    def sample_returns(
            self,
            params: GaussianParams,
            spec: MonteCarloSpec,
    ) -> np.ndarray:
        """Sample ``R = mu + Z @ L.T`` with ``cov = L @ L.T``.

        Parameters
        ----------
        params : GaussianParams
            Calibrated mean and covariance.
        spec : MonteCarloSpec
            Path count, seed, antithetic flag.

        Returns
        -------
        numpy.ndarray
            Returns with shape ``(n_paths, n_assets)``.
        """
        spec.validate()
        n_assets = params.n_assets()
        mu = np.asarray(params.mu, dtype=float).reshape(-1)
        cov = np.asarray(params.cov, dtype=float)

        if mu.shape[0] != n_assets:
            raise DataValidationError("params.mu length mismatch.")
        if cov.shape != (n_assets, n_assets):
            raise DataValidationError("params.cov shape mismatch.")

        try:
            chol = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError as exc:
            raise DataValidationError(
                "Covariance must be SPD for Cholesky sampling."
            ) from exc

        rng = np.random.default_rng(spec.seed)
        if spec.antithetic:
            n_half = spec.n_paths // 2
            z_half = rng.standard_normal(size=(n_half, n_assets))
            z_paths = np.vstack((z_half, -z_half))
        else:
            z_paths = rng.standard_normal(size=(spec.n_paths, n_assets))

        # R = mu + Z @ L.T  (rows are paths)
        return mu + z_paths @ chol.T

    def sample_losses(
            self,
            params: GaussianParams,
            weights: np.ndarray,
            spec: MonteCarloSpec,
    ) -> np.ndarray:
        """Sample portfolio losses from Gaussian asset returns.

        Parameters
        ----------
        params : GaussianParams
            Calibrated mean and covariance.
        weights : numpy.ndarray
            Portfolio weights aligned to ``params.symbols``.
        spec : MonteCarloSpec
            Path count, seed, antithetic flag.

        Returns
        -------
        numpy.ndarray
            Losses with shape ``(n_paths,)``.
        """
        weight_vector = np.asarray(weights, dtype=float).reshape(-1)
        if weight_vector.shape[0] != params.n_assets():
            raise DataValidationError(
                "weights length must match params.n_assets()."
            )
        returns = self.sample_returns(params, spec)
        return portfolio_losses(returns, weight_vector)
