"""Unit tests for Markdown stress reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from qre.domain.risk import HistoricalRiskResult, RiskSummary
from qre.domain.scenarios import (
    AssetContributions,
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    InstantaneousShockResult,
    StressAnalysisResult,
)
from qre.domain.value_objects import DateRange
from qre.reporting.stress_markdown import MarkdownStressReport


def _hypo_result() -> tuple[StressAnalysisResult, HypotheticalScenario]:
    contrib = AssetContributions(by_symbol={"SPY": 0.2}, total=0.2)
    shock = InstantaneousShockResult(
        portfolio_loss=0.2,
        contributions=contrib,
    )
    result = StressAnalysisResult(
        portfolio_name="spy_only",
        scenario_name="equity_crash",
        scenario_kind="hypothetical",
        contributions=contrib,
        instantaneous=shock,
        historical=None,
    )
    scenario = HypotheticalScenario(
        name="equity_crash",
        description="test",
        asset_shocks={"SPY": -0.20},
        vol_multiplier=1.5,
        correlation_inflation=0.3,
        apply_to_historical=False,
    )
    return result, scenario


def test_render_contains_shock_and_caveats() -> None:
    """Rendered stress Markdown includes contributions and caveats."""
    result, scenario = _hypo_result()
    text = MarkdownStressReport().render(result, {"SPY": 1.0}, scenario)
    assert "spy_only" in text
    assert "equity_crash" in text
    assert "SPY" in text
    assert "0.200000" in text
    assert "Caveats" in text
    assert "Euler" in text


def test_write_creates_file(tmp_path: Path) -> None:
    """write() creates parent dirs and a UTF-8 report file."""
    result, scenario = _hypo_result()
    path = tmp_path / "stress" / "run1" / "report.md"
    written = MarkdownStressReport().write(
        result,
        {"SPY": 1.0},
        scenario,
        path,
    )
    assert written.is_file()
    assert "Instantaneous shock" in written.read_text(encoding="utf-8")


def test_episode_render_includes_window() -> None:
    """Episode scenario parameters include the date window."""
    contrib = AssetContributions(by_symbol={"SPY": 0.1}, total=0.1)
    summary = RiskSummary(
        mean_loss=0.01,
        var_by_alpha={0.95: 0.02},
        es_by_alpha={0.95: 0.03},
    )
    historical = HistoricalRiskResult(
        portfolio_name="spy_only",
        n_obs=3,
        start_date="2020-02-20",
        end_date="2020-03-01",
        notional=1_000_000.0,
        summary=summary,
    )
    result = StressAnalysisResult(
        portfolio_name="spy_only",
        scenario_name="covid_window",
        scenario_kind="historical_episode",
        contributions=contrib,
        instantaneous=None,
        historical=historical,
    )
    scenario = HistoricalEpisodeScenario(
        name="covid_window",
        window=DateRange(start=date(2020, 2, 15), end=date(2020, 4, 15)),
        description="COVID",
    )
    text = MarkdownStressReport().render(result, {"SPY": 1.0}, scenario)
    assert "2020-02-15" in text
    assert "VaR=" in text
