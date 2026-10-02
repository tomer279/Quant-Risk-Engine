"""Load stress scenario definitions from YAML files.

Exports
-------
load_scenario_yaml
    Parse a scenario YAML into a ``ScenarioSpec``.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from qre.domain.enums import ScenarioKind
from qre.domain.errors import ConfigError
from qre.domain.scenarios import (
    DEFAULT_APPLY_TO_HISTORICAL,
    DEFAULT_CORR_INFLATION,
    DEFAULT_VOL_MULTIPLIER,
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    ScenarioSpec,
)
from qre.domain.value_objects import DateRange

KIND_EPISODE = ScenarioKind.HISTORICAL_EPISODE.value
KIND_HYPOTHETICAL = ScenarioKind.HYPOTHETICAL.value


def load_scenario_yaml(path: Path | str) -> ScenarioSpec:
    """Load a scenario YAML into a domain scenario spec.

    Parameters
    ----------
    path : pathlib.Path or str
        Path to the scenario YAML.

    Returns
    -------
    ScenarioSpec
        ``HistoricalEpisodeScenario`` or ``HypotheticalScenario``.

    Raises
    ------
    ConfigError
        If the file is missing, unreadable, or structurally invalid.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Scenario file not found: {config_path}")

    try:
        raw = _read_mapping(config_path)
    except OSError as exc:
        raise ConfigError(
            f"Could not read scenario file: {config_path}"
        ) from exc

    name = _require_str(raw, "name")
    kind = _require_str(raw, "kind")
    description = str(raw.get("description", "")).strip()

    if kind == KIND_EPISODE:
        return _build_episode(name, description, raw)
    if kind == KIND_HYPOTHETICAL:
        return _build_hypothetical(name, description, raw)
    raise ConfigError(
        f"Unsupported scenario kind {kind!r}; "
        f"expected {KIND_EPISODE!r} or {KIND_HYPOTHETICAL!r}."
    )


def _build_episode(
    name: str,
    description: str,
    raw: dict[str, Any],
) -> HistoricalEpisodeScenario:
    start = _require_date(raw, "start")
    end = _require_date(raw, "end")
    window = DateRange(start=start, end=end)
    return HistoricalEpisodeScenario(
        name=name,
        window=window,
        description=description,
    )


def _build_hypothetical(
    name: str,
    description: str,
    raw: dict[str, Any],
) -> HypotheticalScenario:
    shocks = _require_asset_shocks(raw)
    vol_multiplier = float(
        raw.get("vol_multiplier", DEFAULT_VOL_MULTIPLIER)
    )
    corr_inflation = float(
        raw.get("correlation_inflation", DEFAULT_CORR_INFLATION)
    )
    apply_hist = bool(
        raw.get("apply_to_historical", DEFAULT_APPLY_TO_HISTORICAL)
    )
    _validate_hypo_params(vol_multiplier, corr_inflation)
    return HypotheticalScenario(
        name=name,
        description=description,
        asset_shocks=shocks,
        vol_multiplier=vol_multiplier,
        correlation_inflation=corr_inflation,
        apply_to_historical=apply_hist,
    )


def _validate_hypo_params(vol_multiplier: float, corr_inflation: float) -> None:
    if vol_multiplier <= 0.0 or not _is_finite(vol_multiplier):
        raise ConfigError("vol_multiplier must be a finite number > 0.")
    if not 0.0 <= corr_inflation <= 1.0 or not _is_finite(corr_inflation):
        raise ConfigError(
            "correlation_inflation must be a finite number in [0, 1]."
        )


def _read_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ConfigError(f"Scenario root must be a mapping: {path}")
    return loaded


def _require_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Scenario field '{key}' must be a non-empty string.")
    return value.strip()


def _require_date(raw: dict[str, Any], key: str) -> date:
    value = raw.get(key)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ConfigError(
                f"Scenario field '{key}' must be an ISO date (YYYY-MM-DD)."
            ) from exc
    raise ConfigError(f"Scenario field '{key}' must be an ISO date string.")


def _require_asset_shocks(raw: dict[str, Any]) -> dict[str, float]:
    shocks = raw.get("asset_shocks")
    if not isinstance(shocks, dict) or not shocks:
        raise ConfigError(
            "Hypothetical scenario 'asset_shocks' must be a non-empty mapping."
        )
    parsed: dict[str, float] = {}
    for ticker, shock in shocks.items():
        if not isinstance(ticker, str) or not ticker.strip():
            raise ConfigError("asset_shocks keys must be non-empty ticker strings.")
        try:
            parsed[ticker.strip().upper()] = float(shock)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"Invalid shock for asset {ticker!r}."
            ) from exc
        if not _is_finite(parsed[ticker.strip().upper()]):
            raise ConfigError(f"Shock for asset {ticker!r} must be finite.")
    return parsed


def _is_finite(value: float) -> bool:
    return math.isfinite(value)
