"""Domain layer: entities, value objects, protocols, and errors.

Exports
-------
QreError, ConfigError, DataValidationError, PortfolioError
    Platform error types.
Symbol, DateRange, Weights
    Immutable value objects.
Position, Portfolio, DatasetRef
    Core domain entities.

Notes
-----
Protocols live in ``qre.domain.protocols`` and are imported from there
rather than re-exported here.
"""

from qre.domain.entities import DatasetRef, Portfolio, Position
from qre.domain.enums import ScenarioKind
from qre.domain.errors import (
    ConfigError,
    DataValidationError,
    ModelCalibrationError,
    PortfolioError,
    QreError,
)
from qre.domain.risk import (
    CalibrationWindow,
    HistoricalRiskResult,
    MonteCarloRiskResult,
    MonteCarloRunConfig,
    RiskSummary,
)
from qre.domain.scenarios import (
    AssetContributions,
    HistoricalEpisodeScenario,
    HypotheticalScenario,
    InstantaneousShockResult,
    ScenarioSpec,
    StressAnalysisResult,
)
from qre.domain.value_objects import DateRange, Symbol, Weights

__all__ = [
    "ConfigError",
    "DataValidationError",
    "DatasetRef",
    "DateRange",
    "Portfolio",
    "PortfolioError",
    "Position",
    "QreError",
    "Symbol",
    "Weights",
    "HistoricalRiskResult",
    "RiskSummary",
    "HistoricalEpisodeScenario",
    "HypotheticalScenario",
    "ScenarioSpec",
    "AssetContributions",
    "InstantaneousShockResult",
    "StressAnalysisResult",
    "ScenarioKind",
    "ModelCalibrationError",
    "MonteCarloRiskResult",
    "MonteCarloRunConfig",
    "CalibrationWindow",
]
