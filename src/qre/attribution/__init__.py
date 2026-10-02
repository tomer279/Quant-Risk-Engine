"""Portfolio attribution helpers.

Exports
-------
CONTRIB_HOW_SUM, CONTRIB_HOW_MEAN
    Aggregation mode constants.
contributions_from_returns
    Time-series linear contributions.
aggregate_contributions
    Collapse contributions to ``AssetContributions``.
"""

from qre.attribution.linear import (
    CONTRIB_HOW_MEAN,
    CONTRIB_HOW_SUM,
    aggregate_contributions,
    contributions_from_returns,
)

__all__ = [
    "CONTRIB_HOW_MEAN",
    "CONTRIB_HOW_SUM",
    "aggregate_contributions",
    "contributions_from_returns",
]
