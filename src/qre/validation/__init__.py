"""Analytic benchmarks and Monte Carlo diagnostics.

Exports
-------
portfolio_loss_moments
    Loss mean and vol under a Gaussian portfolio map.
gaussian_var
    Closed-form Gaussian VaR.
gaussian_es
    Closed-form Gaussian ES.
gaussian_var_es
    VaR and ES for one alpha.
ConvergencePoint
    VaR/ES snapshot at one path count.
convergence_from_losses
    Prefix-based MC convergence table.
"""

from qre.validation.convergence import (
    ConvergencePoint,
    convergence_from_losses,
)
from qre.validation.gaussian_analytic import (
    gaussian_es,
    gaussian_var,
    gaussian_var_es,
    portfolio_loss_moments,
)

__all__ = [
    "ConvergencePoint",
    "convergence_from_losses",
    "gaussian_es",
    "gaussian_var",
    "gaussian_var_es",
    "portfolio_loss_moments",
]
