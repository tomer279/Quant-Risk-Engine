"""Unit tests for MC convergence prefixes."""

from __future__ import annotations

import numpy as np
import pytest

from qre.domain.errors import DataValidationError
from qre.validation import convergence_from_losses


def test_convergence_prefix_sizes() -> None:
    """Each point uses the requested prefix length."""
    rng = np.random.default_rng(0)
    losses = rng.normal(size=1_000)
    points = convergence_from_losses(
        losses,
        path_counts=(100, 500, 1_000),
        alphas=(0.95,),
    )
    assert [point.n_paths for point in points] == [100, 500, 1_000]
    assert points[-1].var_by_alpha[0.95] > 0.0


def test_convergence_rejects_too_large_n() -> None:
    """Reject path counts larger than the loss sample."""
    losses = np.array([0.1, 0.2, 0.3])
    with pytest.raises(DataValidationError, match="path count"):
        convergence_from_losses(losses, path_counts=(10,), alphas=(0.95,))
