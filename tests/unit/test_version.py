"""Smoke test for package version metadata."""

from __future__ import annotations

from qre import __version__


def test_version_is_semver_string() -> None:
    """Package version should be the M0 placeholder."""
    assert __version__ == "0.1.0"
