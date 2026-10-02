"""Historical episode helpers for return-matrix windowing.

Exports
-------
filter_returns_by_episode
    Restrict an aligned return matrix to an inclusive date window.
"""

from __future__ import annotations

import pandas as pd

from qre.domain.errors import DataValidationError
from qre.domain.value_objects import DateRange


def filter_returns_by_episode(
        returns: pd.DataFrame,
        window: DateRange,
) -> pd.DataFrame:
    """Filter return rows to ``[window.start, window.end]`` inclusive.

    Parameters
    ----------
    returns : pandas.DataFrame
        Aligned simple returns; index must be datetime-like.
    window : DateRange
        Inclusive calendar window (from the episode scenario).

    Returns
    -------
    pandas.DataFrame
        Rows whose timestamps fall inside the window. Column order
        unchanged.

    Raises
    ------
    DataValidationError
        If ``returns`` is empty, the index is not datetime-like, or the
        filtered window has no rows.
    """
    if returns.empty:
        raise DataValidationError("Return matrix must be non-empty.")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise DataValidationError(
            "Return matrix index must be a DatetimeIndex for episode filter."
        )

    start_ts = pd.Timestamp(window.start)
    end_ts = pd.Timestamp(window.end)
    if returns.index.tz is not None:
        start_ts = start_ts.tz_localize(returns.index.tz)
        end_ts = end_ts.tz_localize(returns.index.tz)

    filtered = returns.loc[start_ts:end_ts]
    if filtered.empty:
        start_iso, end_iso = window.to_iso_pair()
        raise DataValidationError(
            "Episode window contains no return rows "
            f"(start={start_iso}, end={end_iso})."
        )
    return filtered
