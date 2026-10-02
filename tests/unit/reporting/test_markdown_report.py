"""Unit tests for Markdown historical reports."""

from __future__ import annotations

from pathlib import Path

from qre.domain.risk import HistoricalRiskResult, RiskSummary
from qre.reporting import MarkdownHistoricalReport


def _sample_result() -> HistoricalRiskResult:
    """Build a tiny result for render/write tests."""
    summary = RiskSummary(
        mean_loss=0.01,
        var_by_alpha={0.95: 0.02},
        es_by_alpha={0.95: 0.03},
    )
    return HistoricalRiskResult(
        portfolio_name="toy",
        n_obs=5,
        start_date="2020-01-03",
        end_date="2020-01-10",
        notional=1_000_000.0,
        summary=summary,
    )


def test_render_contains_key_sections() -> None:
    """Rendered Markdown includes portfolio, measures, and caveats."""
    text = MarkdownHistoricalReport().render(
        _sample_result(),
        {"AAA": 0.5, "BBB": 0.5},
    )
    assert "toy" in text
    assert "VaR=" in text
    assert "ES=" in text
    assert "Caveats" in text


def test_write_creates_file(tmp_path: Path) -> None:
    """write() creates parent dirs and a UTF-8 report file."""
    path = tmp_path / "historical" / "run1" / "report.md"
    written = MarkdownHistoricalReport().write(
        _sample_result(),
        {"AAA": 1.0},
        path,
    )
    assert written.is_file()
    assert "Mean loss" in written.read_text(encoding="utf-8")
