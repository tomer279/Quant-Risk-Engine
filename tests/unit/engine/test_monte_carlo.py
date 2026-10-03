"""Unit tests for Gaussian Monte Carlo sampling."""

from __future__ import annotations

import numpy as np
import pytest

from qre.domain.errors import DataValidationError
from qre.engine import GaussianMonteCarloEngine, MonteCarloSpec
from qre.models import GaussianParams


def _identity_params(n_assets: int = 2) -> GaussianParams:
    symbols = tuple(f"A{i}" for i in range(n_assets))
    return GaussianParams(
        mu=np.zeros(n_assets, dtype=float),
        cov=np.eye(n_assets, dtype=float),
        symbols=symbols,
    )


def test_same_seed_reproducible() -> None:
    """Identical seed and spec yield identical paths."""
    engine = GaussianMonteCarloEngine()
    params = _identity_params()
    spec = MonteCarloSpec(n_paths=128, seed=42, antithetic=False)

    first = engine.sample_returns(params, spec)
    second = engine.sample_returns(params, spec)
    np.testing.assert_array_equal(first, second)


def test_different_seed_changes_draws() -> None:
    """Different seeds should not produce identical samples."""
    engine = GaussianMonteCarloEngine()
    params = _identity_params()
    a = engine.sample_returns(params, MonteCarloSpec(64, seed=1))
    b = engine.sample_returns(params, MonteCarloSpec(64, seed=2))
    assert not np.array_equal(a, b)


def test_antithetic_pairs_negate() -> None:
    """With mu=0, antithetic block is exact negation of the first half."""
    engine = GaussianMonteCarloEngine()
    params = _identity_params()
    spec = MonteCarloSpec(n_paths=100, seed=7, antithetic=True)

    paths = engine.sample_returns(params, spec)
    n_half = spec.n_paths // 2
    first = paths[:n_half]
    second = paths[n_half:]
    np.testing.assert_allclose(second, -first)


def test_antithetic_odd_paths_raise() -> None:
    """Odd n_paths is rejected when antithetic is on."""
    spec = MonteCarloSpec(n_paths=5, seed=0, antithetic=True)
    with pytest.raises(DataValidationError, match="even"):
        GaussianMonteCarloEngine().sample_returns(_identity_params(), spec)


def test_sample_losses_shape_and_sign() -> None:
    """Losses have shape (n_paths,) and match -R @ w."""
    engine = GaussianMonteCarloEngine()
    params = GaussianParams(
        mu=np.array([0.01, -0.02]),
        cov=np.array([[0.04, 0.01], [0.01, 0.09]]),
        symbols=("AAA", "BBB"),
    )
    weights = np.array([0.6, 0.4], dtype=float)
    spec = MonteCarloSpec(n_paths=256, seed=99, antithetic=False)

    returns = engine.sample_returns(params, spec)
    losses = engine.sample_losses(params, weights, spec)
    expected = -(returns @ weights)

    assert losses.shape == (spec.n_paths,)
    np.testing.assert_allclose(losses, expected)


def test_sample_mean_near_mu() -> None:
    """Large-N sample mean is close to calibrated mu."""
    engine = GaussianMonteCarloEngine()
    mu = np.array([0.02, -0.01], dtype=float)
    params = GaussianParams(
        mu=mu,
        cov=np.eye(2) * 0.01,
        symbols=("AAA", "BBB"),
    )
    spec = MonteCarloSpec(n_paths=20_000, seed=123, antithetic=True)
    paths = engine.sample_returns(params, spec)
    np.testing.assert_allclose(paths.mean(axis=0), mu, atol=3e-3)


def test_weight_mismatch_raises() -> None:
    """sample_losses rejects misaligned weights."""
    engine = GaussianMonteCarloEngine()
    params = _identity_params(n_assets=2)
    spec = MonteCarloSpec(n_paths=10, seed=0)
    with pytest.raises(DataValidationError, match="weights length"):
        engine.sample_losses(params, np.array([1.0]), spec)
