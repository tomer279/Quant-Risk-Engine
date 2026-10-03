"""MC VaR/ES must match closed-form Gaussian within tolerance."""

from __future__ import annotations

import numpy as np
import pytest

from qre.engine import GaussianMonteCarloEngine, MonteCarloSpec
from qre.measures.empirical import expected_shortfall, var
from qre.models import GaussianParams
from qre.validation import gaussian_es, gaussian_var, portfolio_loss_moments

N_PATHS = 100_000
SEED = 12345
ALPHA = 0.95
REL_TOL = 0.02


def test_mc_var_es_near_analytic() -> None:
    """Large-N MC VaR/ES within relative tolerance of closed form."""
    params = GaussianParams(
        mu=np.array([0.001, -0.0005, 0.0002]),
        cov=np.array(
            [
                [0.0004, 0.0001, 0.0000],
                [0.0001, 0.0009, 0.0002],
                [0.0000, 0.0002, 0.0006],
            ]
        ),
        symbols=("AAA", "BBB", "CCC"),
    )
    weights = np.array([0.5, 0.3, 0.2], dtype=float)
    spec = MonteCarloSpec(
        n_paths=N_PATHS,
        seed=SEED,
        antithetic=True,
    )

    losses = GaussianMonteCarloEngine().sample_losses(params, weights, spec)
    mu_l, sigma_l = portfolio_loss_moments(params.mu, params.cov, weights)

    analytic_var = gaussian_var(mu_l, sigma_l, ALPHA)
    analytic_es = gaussian_es(mu_l, sigma_l, ALPHA)
    mc_var = var(losses, ALPHA)
    mc_es = expected_shortfall(losses, ALPHA)

    assert mc_var == pytest.approx(analytic_var, rel=REL_TOL)
    assert mc_es == pytest.approx(analytic_es, rel=REL_TOL)
