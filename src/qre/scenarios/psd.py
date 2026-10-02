"""Positive-semidefinite projection helpers.

Exports
-------
DEFAULT_PSD_EPSILON
    Floor applied to eigenvalues during projection.
nearest_psd
    Symmetrize and clip eigenvalues to obtain a PSD matrix.
matrix_sqrt
    Symmetric square root of a PSD matrix via eigendecomposition.
matrix_inv_sqrt
    Symmetric inverse square root via eigendecomposition.
"""

from __future__ import annotations

import numpy as np

from qre.domain.errors import DataValidationError

DEFAULT_PSD_EPSILON = 1e-10
HALF = 0.5


def nearest_psd(
        matrix: np.ndarray,
        epsilon: float = DEFAULT_PSD_EPSILON,
) -> np.ndarray:
    """Project a square matrix onto the PSD cone.

    Symmetrize ``(A + A.T) / 2``, eigendecompose, replace each
    eigenvalue ``λ`` with ``max(λ, epsilon)``, then reconstruct.

    Parameters
    ----------
    matrix : numpy.ndarray
        Square real matrix (typically a covariance).
    epsilon : float
        Eigenvalue floor; must be finite and ``>= 0``.

    Returns
    -------
    numpy.ndarray
        Symmetric PSD matrix of the same shape.

    Raises
    ------
    DataValidationError
        If ``matrix`` is not 2-D square or ``epsilon`` is invalid.
    """
    _validate_square(matrix)
    if epsilon < 0.0 or not np.isfinite(epsilon):
        raise DataValidationError(
            "PSD epsilon must be a finite number >= 0."
        )

    symmetric = HALF * (matrix + matrix.T)
    eigvals, eigvecs = np.linalg.eigh(symmetric)
    eigvals = np.maximum(eigvals, epsilon)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def matrix_sqrt(
        matrix: np.ndarray,
        epsilon: float = DEFAULT_PSD_EPSILON,
) -> np.ndarray:
    """Return the symmetric square root of a PSD matrix.

    Parameters
    ----------
    matrix : numpy.ndarray
        Square matrix (projected to PSD first).
    epsilon : float
        Eigenvalue floor used before taking square roots.

    Returns
    -------
    numpy.ndarray
        ``S`` such that ``S @ S`` approximates the PSD projection of
        ``matrix``.
    """
    psd = nearest_psd(matrix, epsilon=epsilon)
    eigvals, eigvecs = np.linalg.eigh(psd)
    sqrt_vals = np.sqrt(np.maximum(eigvals, 0.0))
    return eigvecs @ np.diag(sqrt_vals) @ eigvecs.T


def matrix_inv_sqrt(
        matrix: np.ndarray,
        epsilon: float = DEFAULT_PSD_EPSILON,
) -> np.ndarray:
    """Return the symmetric inverse square root of a PSD matrix.

    Parameters
    ----------
    matrix : numpy.ndarray
        Square matrix (projected to PSD first).
    epsilon : float
        Eigenvalue floor before reciprocating square roots.

    Returns
    -------
    numpy.ndarray
        ``S_inv`` approximating ``matrix^{-1/2}``.
    """
    psd = nearest_psd(matrix, epsilon=epsilon)
    eigvals, eigvecs = np.linalg.eigh(psd)
    eigvals = np.maximum(eigvals, epsilon)
    inv_sqrt_vals = 1.0 / np.sqrt(eigvals)
    return eigvecs @ np.diag(inv_sqrt_vals) @ eigvecs.T


def _validate_square(matrix: np.ndarray) -> None:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise DataValidationError(
            "Matrix must be 2-D square for PSD operations."
        )
