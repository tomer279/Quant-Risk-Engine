"""Risk model adapters.

Exports
-------
HistoricalSimulationModel
    Historical simulation loss generator.
GaussianParams
    Calibrated Gaussian mean and covariance.
GaussianReturnModel
    Multivariate Gaussian calibration adapter.
"""

from qre.models.gaussian import GaussianParams, GaussianReturnModel
from qre.models.historical import HistoricalSimulationModel

__all__ = [
    "GaussianParams",
    "GaussianReturnModel",
    "HistoricalSimulationModel",
]
