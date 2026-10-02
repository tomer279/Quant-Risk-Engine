"""Unit tests for scenario domain types."""

from __future__ import annotations

from datetime import date

from qre.domain.enums import ScenarioKind
from qre.domain.scenarios import (
    AssetContributions,
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    InstantaneousShockResult,
    StressAnalysisResult,
)
from qre.domain.value_objects import DateRange


def test_scenario_kind_helpers() -> None:
    """ScenarioKind helpers distinguish episode vs hypothetical."""
    episode: ScenarioKind = ScenarioKind.HISTORICAL_EPISODE
    hypo: ScenarioKind = ScenarioKind.HYPOTHETICAL
    assert episode.is_episode()
    assert not episode.is_hypothetical()
    assert hypo.is_hypothetical()


def test_asset_contributions_as_dict_sorted() -> None:
    """symbols() and as_dict() use sorted ticker keys."""
    contrib = AssetContributions(
        by_symbol={"SPY": 0.08, "QQQ": 0.05},
        total=0.13,
    )
    assert contrib.symbols() == ("QQQ", "SPY")
    assert contrib.as_dict()["total"] == 0.13


def test_episode_as_dict() -> None:
    """Episode as_dict includes kind and ISO dates."""
    scenario = HistoricalEpisodeScenario(
        name="covid_window",
        window=DateRange(start=date(2020, 2, 15), end=date(2020, 4, 15)),
        description="test",
    )
    payload = scenario.as_dict()
    assert payload["kind"] == "historical_episode"
    assert payload["start"] == "2020-02-15"


def test_stress_result_contribution_table() -> None:
    """Contribution table and as_dict expose shock loss."""
    contrib = AssetContributions(by_symbol={"SPY": 0.2}, total=0.2)
    shock = InstantaneousShockResult(
        portfolio_loss=0.2,
        contributions=contrib,
    )
    result = StressAnalysisResult(
        portfolio_name="spy_only",
        scenario_name="equity_crash",
        scenario_kind=ScenarioKind.HYPOTHETICAL.value,
        contributions=contrib,
        instantaneous=shock,
        historical=None,
    )
    table = result.format_contribution_table()
    assert "SPY" in table
    assert "0.200000" in table
    assert result.as_dict()["instantaneous"]["portfolio_loss"] == 0.2


def test_hypothetical_defaults() -> None:
    """HypotheticalScenario uses off-by-default vol/corr knobs."""
    scenario = HypotheticalScenario(
        name="x",
        description="",
        asset_shocks={"SPY": -0.2},
    )
    assert scenario.vol_multiplier == 1.0
    assert scenario.correlation_inflation == 0.0
    assert scenario.apply_to_historical is False
