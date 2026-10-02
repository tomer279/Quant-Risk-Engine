"""Unit tests for nearest-PSD projection helpers."""

from __future__ import annotations

import numpy as np
import pytest

from qre.domain.errors import DataValidationError
from qre.scenarios.psd import (
    DEFAULT_PSD_EPSILON,
    matrix_inv_sqrt,
    matrix_sqrt,
    nearest_psd,
)


def test_nearest_psd_symmetric_nonneg_eigs() -> None:
    """Non-PSD input becomes symmetric with eigenvalues >= epsilon."""
    matrix = np.array([[1.0, 2.0], [2.0, 1.0]], dtype=float)
    psd = nearest_psd(matrix, epsilon=DEFAULT_PSD_EPSILON)
    assert np.allclose(psd, psd.T)
    eigvals = np.linalg.eigvalsh(psd)
    assert np.all(eigvals >= DEFAULT_PSD_EPSILON - 1e-12)


def test_matrix_sqrt_roundtrip() -> None:
    """Symmetric square root satisfies S @ S ≈ A for PSD A."""
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=float)
    sqrt_mat = matrix_sqrt(matrix)
    assert np.allclose(sqrt_mat @ sqrt_mat, matrix, atol=1e-10)


def test_matrix_inv_sqrt_identity() -> None:
    """A^{-1/2} @ A^{1/2} ≈ I for a well-conditioned PSD matrix."""
    matrix = np.array([[4.0, 1.0], [1.0, 3.0]], dtype=float)
    inv_sqrt = matrix_inv_sqrt(matrix)
    sqrt_mat = matrix_sqrt(matrix)
    identity = inv_sqrt @ sqrt_mat
    assert np.allclose(identity, np.eye(2), atol=1e-10)


def test_nearest_psd_rejects_nonsquare() -> None:
    """Non-square matrices raise DataValidationError."""
    with pytest.raises(DataValidationError, match="2-D square"):
        nearest_psd(np.ones((2, 3)))
