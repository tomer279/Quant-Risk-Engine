"""Historical simulation loss generator.

Exports
-------
HistoricalSimulationModel
    Build portfolio loss series from an aligned return matrix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qre.domain.entities import Portfolio
from qre.domain.errors import DataValidationError


class HistoricalSimulationModel:
    """Empirical historical simulation (no calibration).

    Methods
    -------
    weight_vector(portfolio, columns)
        Build a weight vector aligned to return-matrix columns.
    generate_losses(portfolio, return_matrix)
        Return ``L_t = -R_t^T w`` for each row of the return matrix.
    """

    def weight_vector(
            self,
            portfolio: Portfolio,
            columns: tuple[str, ...] | list[str],
    ) -> np.ndarray:
        """Map portfolio weights onto return-matrix column order.

        Parameters
        ----------
        portfolio : Portfolio
            Source of validated weights.
        columns : sequence of str
            Return-matrix ticker columns (must match portfolio exactly
            as a set; order may differ and is respected).

        Returns
        -------
        numpy.ndarray
            1-D weight vector with ``len(columns)`` entries.

        Raises
        ------
        DataValidationError
            If columns and portfolio symbols disagree.
        """
        weights = portfolio.to_weights().as_dict()
        portfolio_tickers = set(weights)
        column_tickers = set(columns)
        if portfolio_tickers != column_tickers:
            missing = sorted(portfolio_tickers - column_tickers)
            extra = sorted(column_tickers - portfolio_tickers)
            raise DataValidationError(
                "Return matrix columns must match portfolio symbols. "
                f"missing={missing}, extra={extra}."
            )
        return np.array(
            [weights[ticker] for ticker in columns],
            dtype=float,
        )

    def generate_losses(
            self,
            portfolio: Portfolio,
            return_matrix: pd.DataFrame,
    ) -> np.ndarray:
        """Compute historical portfolio losses.

        Parameters
        ----------
        portfolio : Portfolio
            Portfolio weights.
        return_matrix : pandas.DataFrame
            Aligned simple returns; columns are tickers.

        Returns
        -------
        numpy.ndarray
            1-D loss sample ``L = -R @ w`` (positive = loss).

        Raises
        ------
        DataValidationError
            If the matrix is empty or columns do not match the portfolio.
        """
        if return_matrix.empty:
            raise DataValidationError("Return matrix must be non-empty.")

        columns = list(return_matrix.columns.astype(str))
        weights = self.weight_vector(portfolio, columns)
        # R shape (T, N), w shape (N,) → portfolio returns (T,)
        portfolio_returns = return_matrix.to_numpy(dtype=float) @ weights
        return -portfolio_returns
