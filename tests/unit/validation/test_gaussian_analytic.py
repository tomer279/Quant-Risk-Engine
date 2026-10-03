"""Unit tests for closed-form Gaussian VaR / ES."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from qre.domain.errors import DataValidationError
from qre.validation.gaussian_analytic import (
    gaussian_es,
    gaussian_var,
    gaussian_var_es,
    portfolio_loss_moments,
)


def test_portfolio_loss_moments_hand_check() -> None:
    """mu_L = -w^T mu and sigma_L = sqrt(w^T cov w)."""
    mu = np.array([0.01, 0.02])
    cov = np.array([[0.04, 0.01], [0.01, 0.09]])
    weights = np.array([0.5, 0.5])

    mu_l, sigma_l = portfolio_loss_moments(mu, cov, weights)
    mu_p = float(weights @ mu)
    var_p = float(weights @ cov @ weights)

    assert mu_l == pytest.approx(-mu_p)
    assert sigma_l == pytest.approx(np.sqrt(var_p))


def test_gaussian_var_es_standard_normal_loss() -> None:
    """For N(0,1) losses, VaR/ES match Phi formulas."""
    alpha = 0.95
    z = norm.ppf(alpha)
    expected_var = z
    expected_es = norm.pdf(z) / (1.0 - alpha)

    assert gaussian_var(0.0, 1.0, alpha) == pytest.approx(expected_var)
    assert gaussian_es(0.0, 1.0, alpha) == pytest.approx(expected_es)
    var_value, es_value = gaussian_var_es(0.0, 1.0, alpha)
    assert var_value == pytest.approx(expected_var)
    assert es_value == pytest.approx(expected_es)


def test_location_scale_shift() -> None:
    """VaR/ES shift as mu_L + sigma_L * standard."""
    mu_l = 0.02
    sigma_l = 0.03
    alpha = 0.99
    base_var = gaussian_var(0.0, 1.0, alpha)
    base_es = gaussian_es(0.0, 1.0, alpha)

    assert gaussian_var(mu_l, sigma_l, alpha) == pytest.approx(
        mu_l + sigma_l * base_var
    )
    assert gaussian_es(mu_l, sigma_l, alpha) == pytest.approx(
        mu_l + sigma_l * base_es
    )


def test_invalid_alpha_raises() -> None:
    """Reject alpha outside (0, 1)."""
    with pytest.raises(DataValidationError, match="alpha"):
        gaussian_var(0.0, 1.0, 1.0)
