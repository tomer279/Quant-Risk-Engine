"""Empirical and model-based risk measures.

Exports
-------
mean_loss
    Sample mean of losses.
var
    Empirical VaR.
expected_shortfall
    Empirical expected shortfall.
exceedance_probability
    Tail exceedance rate.
summarize_losses
    Bundle mean / VaR / ES.
QUANTILE_METHOD
    Locked NumPy quantile method for M1.
"""

from qre.measures.empirical import (
    QUANTILE_METHOD,
    exceedance_probability,
    expected_shortfall,
    mean_loss,
    summarize_losses,
    var,
)

__all__ = [
    "QUANTILE_METHOD",
    "exceedance_probability",
    "expected_shortfall",
    "mean_loss",
    "summarize_losses",
    "var",
]
