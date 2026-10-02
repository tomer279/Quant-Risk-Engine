"""Unit tests for scenario YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from qre.application.load_scenario import load_scenario_yaml
from qre.domain.enums import ScenarioKind
from qre.domain.errors import ConfigError, DataValidationError
from qre.domain.scenarios import HistoricalEpisodeScenario, HypotheticalScenario


def test_load_covid_window() -> None:
    """COVID YAML loads as a historical episode scenario."""
    path = Path("configs/scenarios/covid_window.yaml")
    scenario = load_scenario_yaml(path)
    assert isinstance(scenario, HistoricalEpisodeScenario)
    assert scenario.name == "covid_window"
    assert scenario.kind() is ScenarioKind.HISTORICAL_EPISODE
    assert scenario.window.start.isoformat() == "2020-02-15"
    assert scenario.window.end.isoformat() == "2020-04-15"


def test_load_equity_crash() -> None:
    """Equity-crash YAML loads shocks and stress parameters."""
    path = Path("configs/scenarios/equity_crash.yaml")
    scenario = load_scenario_yaml(path)
    assert isinstance(scenario, HypotheticalScenario)
    assert scenario.kind() is ScenarioKind.HYPOTHETICAL
    assert scenario.asset_shocks["SPY"] == pytest.approx(-0.20)
    assert scenario.asset_shocks["QQQ"] == pytest.approx(-0.25)
    assert scenario.vol_multiplier == pytest.approx(1.5)
    assert scenario.correlation_inflation == pytest.approx(0.30)
    assert scenario.apply_to_historical is True


def test_missing_file_raises(tmp_path: Path) -> None:
    """Missing scenario path raises ConfigError."""
    with pytest.raises(ConfigError, match="not found"):
        load_scenario_yaml(tmp_path / "missing.yaml")


def test_bad_kind_raises(tmp_path: Path) -> None:
    """Unknown scenario kind raises ConfigError."""
    path = tmp_path / "bad_kind.yaml"
    path.write_text(
        "name: x\nkind: monte_carlo\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="Unsupported scenario kind"):
        load_scenario_yaml(path)


def test_bad_vol_multiplier_raises(tmp_path: Path) -> None:
    """Non-positive vol_multiplier raises ConfigError."""
    path = tmp_path / "bad_vol.yaml"
    path.write_text(
        "name: x\nkind: hypothetical\n"
        "asset_shocks:\n  SPY: -0.1\n"
        "vol_multiplier: 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="vol_multiplier"):
        load_scenario_yaml(path)


def test_bad_corr_inflation_raises(tmp_path: Path) -> None:
    """correlation_inflation outside [0, 1] raises ConfigError."""
    path = tmp_path / "bad_corr.yaml"
    path.write_text(
        "name: x\nkind: hypothetical\n"
        "asset_shocks:\n  SPY: -0.1\n"
        "correlation_inflation: 1.5\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="correlation_inflation"):
        load_scenario_yaml(path)


def test_inverted_episode_dates_raise(tmp_path: Path) -> None:
    """Episode start after end raises a validation/config error."""
    path = tmp_path / "bad_dates.yaml"
    path.write_text(
        "name: x\nkind: historical_episode\n"
        'start: "2020-04-15"\n'
        'end: "2020-02-15"\n',
        encoding="utf-8",
    )
    with pytest.raises((ConfigError, DataValidationError)):
        load_scenario_yaml(path)
