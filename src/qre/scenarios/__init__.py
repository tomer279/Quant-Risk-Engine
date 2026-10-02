"""Scenario transforms for stress testing.

Exports
-------
filter_returns_by_episode
    Date-window filter for historical episode replay.
HypoStressParams
    Vol / correlation stress parameter bundle.
apply_asset_shocks
    Instantaneous shock loss and linear contributions.
estimate_covariance
    Sample covariance of a return matrix.
correlation_from_covariance
    Covariance to correlation with unit diagonal.
inflate_correlation
    Blend correlations toward all-ones.
build_covariance
    Rebuild covariance from vols and correlation.
apply_vol_and_corr_stress
    Base and stressed covariances with PSD projection.
recolor_returns
    Recolor demeaned returns to a stressed covariance.
DEFAULT_PSD_EPSILON
    Default eigenvalue floor for PSD helpers.
nearest_psd
    Nearest symmetric PSD projection.
matrix_sqrt
    Symmetric matrix square root.
matrix_inv_sqrt
    Symmetric inverse square root.
"""

from qre.scenarios.historical_episode import filter_returns_by_episode
from qre.scenarios.hypothetical import (
    HypoStressParams,
    apply_asset_shocks,
    apply_vol_and_corr_stress,
    build_covariance,
    correlation_from_covariance,
    estimate_covariance,
    inflate_correlation,
    recolor_returns,
)
from qre.scenarios.psd import (
    DEFAULT_PSD_EPSILON,
    matrix_inv_sqrt,
    matrix_sqrt,
    nearest_psd,
)

__all__ = [
    "DEFAULT_PSD_EPSILON",
    "HypoStressParams",
    "apply_asset_shocks",
    "apply_vol_and_corr_stress",
    "build_covariance",
    "correlation_from_covariance",
    "estimate_covariance",
    "filter_returns_by_episode",
    "inflate_correlation",
    "matrix_inv_sqrt",
    "matrix_sqrt",
    "nearest_psd",
    "recolor_returns",
]
