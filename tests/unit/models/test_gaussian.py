"""Unit tests for GaussianReturnModel calibration."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qre.domain.errors import ModelCalibrationError
from qre.models import GaussianParams, GaussianReturnModel


def _toy_returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AAA": [0.01, 0.02, -0.01, 0.00],
            "BBB": [0.00, 0.01, 0.01, -0.02],
        }
    )


def test_calibrate_stores_params() -> None:
    """calibrate returns params and params() echoes them."""
    model = GaussianReturnModel()
    frame = _toy_returns()
    fitted = model.calibrate(frame)
    stored = model.params()

    assert isinstance(fitted, GaussianParams)
    assert fitted.symbols == ("AAA", "BBB")
    assert fitted.n_assets() == 2
    np.testing.assert_allclose(stored.mu, fitted.mu)
    np.testing.assert_allclose(stored.cov, fitted.cov)


def test_params_before_calibrate_raises() -> None:
    """params() without calibrate raises ModelCalibrationError."""
    model = GaussianReturnModel()
    with pytest.raises(ModelCalibrationError, match="not been calibrated"):
        model.params()


def test_calibrate_preserves_column_order() -> None:
    """Symbol order follows the return-matrix columns."""
    frame = pd.DataFrame(
        {
            "BBB": [0.0, 0.2, -0.1],
            "AAA": [0.1, -0.1, 0.0],
        }
    )
    params = GaussianReturnModel().calibrate(frame)
    assert params.symbols == ("BBB", "AAA")
    np.testing.assert_allclose(params.mu[0], frame["BBB"].mean())
    np.testing.assert_allclose(params.mu[1], frame["AAA"].mean())


def test_calibrate_empty_raises_model_error() -> None:
    """Empty input becomes ModelCalibrationError."""
    model = GaussianReturnModel()
    frame = pd.DataFrame(columns=["AAA", "BBB"])
    with pytest.raises(ModelCalibrationError):
        model.calibrate(frame)


def test_gaussian_params_as_dict() -> None:
    """as_dict is JSON-friendly."""
    params = GaussianParams(
        mu=np.array([0.1, 0.2]),
        cov=np.array([[1.0, 0.0], [0.0, 1.0]]),
        symbols=("AAA", "BBB"),
    )
    payload = params.as_dict()
    assert payload["symbols"] == ["AAA", "BBB"]
    assert payload["mu"] == [0.1, 0.2]
    assert payload["cov"] == [[1.0, 0.0], [0.0, 1.0]]
