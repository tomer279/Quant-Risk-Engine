"""Unit tests for hypothetical shocks and vol/corr stress."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qre.domain.entities import Portfolio
from qre.domain.errors import DataValidationError
from qre.domain.value_objects import Weights
from qre.scenarios.hypothetical import (
    HypoStressParams,
    apply_asset_shocks,
    apply_vol_and_corr_stress,
    estimate_covariance,
    inflate_correlation,
    recolor_returns,
)
from qre.scenarios.psd import nearest_psd


def test_spy_only_shock_loss() -> None:
    """100% SPY with -20% shock → loss ≈ 0.20 (M2 exit sanity)."""
    weights = Weights.from_mapping({"SPY": 1.0})
    portfolio = Portfolio.from_weights("spy_only", weights)
    result = apply_asset_shocks(portfolio, {"SPY": -0.20})
    assert result.portfolio_loss == pytest.approx(0.20)
    assert result.contributions.by_symbol["SPY"] == pytest.approx(0.20)
    assert result.contributions.total == pytest.approx(0.20)


def test_missing_shock_treated_as_zero() -> None:
    """Assets without an explicit shock contribute zero."""
    weights = Weights.from_mapping({"SPY": 0.5, "TLT": 0.5})
    portfolio = Portfolio.from_weights("half", weights)
    result = apply_asset_shocks(portfolio, {"SPY": -0.20})
    assert result.contributions.by_symbol["SPY"] == pytest.approx(0.10)
    assert result.contributions.by_symbol["TLT"] == pytest.approx(0.0)
    assert result.portfolio_loss == pytest.approx(0.10)


def test_extra_shock_ticker_raises() -> None:
    """Shocks for tickers outside the portfolio raise."""
    weights = Weights.from_mapping({"SPY": 1.0})
    portfolio = Portfolio.from_weights("spy_only", weights)
    with pytest.raises(DataValidationError, match="not in portfolio"):
        apply_asset_shocks(portfolio, {"SPY": -0.1, "QQQ": -0.1})


def test_inflate_correlation_unit_diagonal() -> None:
    """Inflated correlation stays symmetric with unit diagonal."""
    corr = np.array([[1.0, 0.2], [0.2, 1.0]], dtype=float)
    inflated = inflate_correlation(corr, lambda_=0.5)
    assert np.allclose(inflated, inflated.T)
    assert np.allclose(np.diag(inflated), np.ones(2))
    assert inflated[0, 1] == pytest.approx(0.6)
    eigvals = np.linalg.eigvalsh(nearest_psd(inflated))
    assert np.all(eigvals >= -1e-12)


def test_vol_multiplier_scales_variances() -> None:
    """With λ=0, vol multiplier m scales variances by m^2."""
    rng = np.random.default_rng(42)
    raw = rng.normal(size=(400, 2))
    returns = pd.DataFrame(raw, columns=["A", "B"])
    params = HypoStressParams(
        vol_multiplier=2.0,
        correlation_inflation=0.0,
    )
    cov_base, cov_stressed = apply_vol_and_corr_stress(returns, params)
    assert np.allclose(
        np.diag(cov_stressed),
        np.diag(cov_base) * 4.0,
        rtol=1e-6,
        atol=1e-8,
    )


def test_recolor_moves_sample_toward_stressed_cov() -> None:
    """Recolored sample covariance is close to the stressed target."""
    rng = np.random.default_rng(7)
    n_obs = 800
    cov_true = np.array([[0.04, 0.01], [0.01, 0.09]], dtype=float)
    factor = np.linalg.cholesky(cov_true)
    raw = rng.normal(size=(n_obs, 2)) @ factor.T
    returns = pd.DataFrame(raw, columns=["A", "B"])

    params = HypoStressParams(
        vol_multiplier=1.5,
        correlation_inflation=0.3,
    )
    cov_base, cov_stressed = apply_vol_and_corr_stress(returns, params)
    recolored = recolor_returns(returns, cov_base, cov_stressed)
    sample_cov = estimate_covariance(recolored)
    assert np.allclose(sample_cov, cov_stressed, atol=0.02, rtol=0.15)


def test_hypo_params_inactive() -> None:
    """Default params report as inactive stress."""
    params = HypoStressParams()
    assert params.is_inactive()
    assert not HypoStressParams(vol_multiplier=1.5).is_inactive()
