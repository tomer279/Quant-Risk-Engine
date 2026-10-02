"""Linear P&L asset contribution helpers.

Exports
-------
CONTRIB_HOW_SUM, CONTRIB_HOW_MEAN
    Supported aggregation modes for episode contributions.
contributions_from_returns
    Build ``L_{i,t} = -w_i R_{i,t}`` as a DataFrame.
aggregate_contributions
    Collapse a contribution frame to ``AssetContributions``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qre.domain.entities import Portfolio
from qre.domain.errors import DataValidationError
from qre.domain.scenarios import AssetContributions
from qre.models.historical import HistoricalSimulationModel

CONTRIB_HOW_SUM = "sum"
CONTRIB_HOW_MEAN = "mean"
CONTRIB_ROW_TOLERANCE = 1e-10


def contributions_from_returns(
        portfolio: Portfolio,
        return_matrix: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-asset linear contributions for each date.

    For each asset ``i`` and time ``t``::

        L_{i,t} = - w_i R_{i,t}

    Row sums equal portfolio losses ``L_t = -w^T R_t``.

    Parameters
    ----------
    portfolio : Portfolio
        Validated weights.
    return_matrix : pandas.DataFrame
        Aligned simple returns (columns = tickers).

    Returns
    -------
    pandas.DataFrame
        Same index/columns as ``return_matrix``; values are contributions.

    Raises
    ------
    DataValidationError
        If the matrix is empty or columns do not match the portfolio.
    """
    if return_matrix.empty:
        raise DataValidationError("Return matrix must be non-empty.")

    columns = list(return_matrix.columns.astype(str))
    model = HistoricalSimulationModel()
    weights = model.weight_vector(portfolio, columns)
    returns_values = return_matrix.to_numpy(dtype=float)
    # Broadcasting: (T, N) * (N,) → elementwise w_i R_{i,t}
    contrib_values = -(returns_values * weights)
    return pd.DataFrame(
        contrib_values,
        index=return_matrix.index,
        columns=columns,
    )


def aggregate_contributions(
        contrib_frame: pd.DataFrame,
        how: str = CONTRIB_HOW_SUM,
) -> AssetContributions:
    """Aggregate a contribution time series per asset.

    Parameters
    ----------
    contrib_frame : pandas.DataFrame
        Output of ``contributions_from_returns``.
    how : str
        ``"sum"`` (default; episode P&L) or ``"mean"``.

    Returns
    -------
    AssetContributions
        Per-symbol aggregates and ``total = sum(by_symbol)``.

    Raises
    ------
    DataValidationError
        If the frame is empty or ``how`` is unsupported.
    """
    if contrib_frame.empty:
        raise DataValidationError("Contribution frame must be non-empty.")
    if how == CONTRIB_HOW_SUM:
        series = contrib_frame.sum(axis=0)
    elif how == CONTRIB_HOW_MEAN:
        series = contrib_frame.mean(axis=0)
    else:
        raise DataValidationError(
            f"Unsupported aggregation how={how!r}; "
            f"expected {CONTRIB_HOW_SUM!r} or {CONTRIB_HOW_MEAN!r}."
        )

    by_symbol = {
        str(symbol): float(series[symbol])
        for symbol in series.index
    }
    total = float(sum(by_symbol.values()))
    return AssetContributions(by_symbol=by_symbol, total=total)


def portfolio_losses_from_contributions(
        contrib_frame: pd.DataFrame,
) -> np.ndarray:
    """Row-sum contributions to recover portfolio losses.

    Parameters
    ----------
    contrib_frame : pandas.DataFrame
        Per-asset contribution matrix.

    Returns
    -------
    numpy.ndarray
        1-D portfolio losses ``L_t``.
    """
    return contrib_frame.sum(axis=1).to_numpy(dtype=float)
