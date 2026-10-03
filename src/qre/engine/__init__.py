"""Simulation and portfolio P&L engine primitives.

Exports
-------
portfolio_returns
    Map return paths and weights to portfolio returns.
portfolio_losses
    Map return paths and weights to portfolio losses.
MonteCarloSpec
    Seeded Monte Carlo run configuration.
GaussianMonteCarloEngine
    Cholesky Gaussian path / loss sampler.
"""

from qre.engine.monte_carlo import GaussianMonteCarloEngine, MonteCarloSpec
from qre.engine.portfolio_pnl import portfolio_losses, portfolio_returns

__all__ = [
    "GaussianMonteCarloEngine",
    "MonteCarloSpec",
    "portfolio_losses",
    "portfolio_returns",
]
