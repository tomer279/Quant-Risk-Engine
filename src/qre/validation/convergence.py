"""Monte Carlo convergence diagnostics from a loss sample.

Exports
-------
ConvergencePoint
    VaR/ES at one prefix length.
convergence_from_losses
    Build a convergence table from path-count prefixes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

from qre.domain.errors import DataValidationError
from qre.measures.empirical import expected_shortfall, var


@dataclass(frozen=True, slots=True)
class ConvergencePoint:
    """Empirical risk measures at one Monte Carlo size.

    Parameters
    ----------
    n_paths : int
        Prefix length used for the estimates.
    var_by_alpha : dict of float to float
        Empirical VaR by confidence level.
    es_by_alpha : dict of float to float
        Empirical ES by confidence level.

    Methods
    -------
    alphas()
        Sorted alpha keys.
    as_dict()
        JSON-friendly snapshot.
    """

    n_paths: int
    var_by_alpha: dict[float, float]
    es_by_alpha: dict[float, float]

    def alphas(self) -> tuple[float, ...]:
        """Return sorted confidence levels."""
        return tuple(sorted(self.var_by_alpha))

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON."""
        return {
            "n_paths": self.n_paths,
            "var_by_alpha": {
                str(alpha): value
                for alpha, value in sorted(self.var_by_alpha.items())
            },
            "es_by_alpha": {
                str(alpha): value
                for alpha, value in sorted(self.es_by_alpha.items())
            },
        }


def convergence_from_losses(
        losses: np.ndarray,
        path_counts: Sequence[int],
        alphas: Sequence[float],
) -> tuple[ConvergencePoint, ...]:
    """Compute VaR/ES on increasing prefixes of ``losses``.

    Parameters
    ----------
    losses : numpy.ndarray
        Full 1-D Monte Carlo loss sample.
    path_counts : sequence of int
        Prefix lengths ``n`` with ``1 <= n <= len(losses)``.
    alphas : sequence of float
        Confidence levels in ``(0, 1)``.

    Returns
    -------
    tuple of ConvergencePoint
        One point per requested path count (sorted ascending).
    """
    sample = np.asarray(losses, dtype=float).reshape(-1)
    if sample.size == 0:
        raise DataValidationError("Loss sample must be non-empty.")
    if not path_counts:
        raise DataValidationError("path_counts must be non-empty.")
    if not alphas:
        raise DataValidationError("alphas must be non-empty.")

    points: list[ConvergencePoint] = []
    for n_paths in sorted(path_counts):
        if n_paths < 1 or n_paths > sample.size:
            raise DataValidationError(
                "Each path count must satisfy "
                f"1 <= n <= {sample.size}; got {n_paths}."
            )
        prefix = sample[:n_paths]
        var_by_alpha = {
            float(alpha): var(prefix, float(alpha))
            for alpha in alphas
        }
        es_by_alpha = {
            float(alpha): expected_shortfall(prefix, float(alpha))
            for alpha in alphas
        }
        points.append(
            ConvergencePoint(
                n_paths=int(n_paths),
                var_by_alpha=var_by_alpha,
                es_by_alpha=es_by_alpha,
            )
        )
    return tuple(points)
