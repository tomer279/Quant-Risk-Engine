"""Unit tests for empirical VaR / ES helpers."""

from __future__ import annotations

import numpy as np
import pytest

from qre.domain.errors import DataValidationError
from qre.measures.empirical import (
    QUANTILE_METHOD,
    exceedance_probability,
    expected_shortfall,
    mean_loss,
    summarize_losses,
    var,
)

# Hand-check fixture (document for spreadsheet reproducibility):
# losses = [0.01, 0.02, 0.03, 0.04, 0.10]
# alpha = 0.80
# VaR = numpy.quantile(losses, 0.80, method="linear")
# ES  = mean of losses >= VaR
HAND_LOSSES = np.array([0.01, 0.02, 0.03, 0.04, 0.10], dtype=float)
HAND_ALPHA = 0.80


def test_mean_loss() -> None:
    assert mean_loss(HAND_LOSSES) == pytest.approx(float(np.mean(HAND_LOSSES)))


def test_var_matches_numpy_linear() -> None:
    expected = float(
        np.quantile(HAND_LOSSES, HAND_ALPHA, method=QUANTILE_METHOD)
    )
    assert var(HAND_LOSSES, HAND_ALPHA) == pytest.approx(expected)


def test_expected_shortfall_tail_mean() -> None:
    threshold = float(
        np.quantile(HAND_LOSSES, HAND_ALPHA, method=QUANTILE_METHOD)
    )
    tail = HAND_LOSSES[HAND_LOSSES >= threshold]
    assert expected_shortfall(HAND_LOSSES, HAND_ALPHA) == pytest.approx(
        float(np.mean(tail))
    )


def test_exceedance_probability() -> None:
    # Strictly above 0.03 → {0.04, 0.10} → 2/5
    assert exceedance_probability(HAND_LOSSES, 0.03) == pytest.approx(0.4)


def test_summarize_losses_keys() -> None:
    summary = summarize_losses(HAND_LOSSES, [0.8, 0.9])
    assert summary.alphas() == (0.8, 0.9)
    assert 0.8 in summary.var_by_alpha
    assert 0.8 in summary.es_by_alpha


def test_invalid_alpha_raises() -> None:
    with pytest.raises(DataValidationError, match="0 < alpha < 1"):
        var(HAND_LOSSES, 1.0)


def test_empty_losses_raise() -> None:
    with pytest.raises(DataValidationError, match="non-empty"):
        mean_loss(np.array([], dtype=float))
