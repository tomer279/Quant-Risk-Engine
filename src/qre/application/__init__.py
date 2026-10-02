"""Application use-cases for the Quant Risk Engine.

Exports
-------
IngestDeps
    Source/store dependency pair.
ingest_symbol
    Ingest a single symbol.
ingest_universe
    Ingest a symbol list.
"""

from qre.application.ingest_market_data import (
    IngestDeps,
    ingest_symbol,
    ingest_universe,
)
from qre.application.load_portfolio import PortfolioSpec, load_portfolio_yaml
from qre.application.load_scenario import load_scenario_yaml
from qre.application.run_historical_analysis import (
    AnalysisDeps,
    run_historical_analysis,
)
from qre.application.run_stress_analysis import (
    StressAnalysisOutcome,
    run_stress_analysis,
)

__all__ = [
    "IngestDeps",
    "ingest_symbol",
    "ingest_universe",
    "PortfolioSpec",
    "load_portfolio_yaml",
    "load_scenario_yaml",
    "AnalysisDeps",
    "run_historical_analysis",
    "StressAnalysisOutcome",
    "run_stress_analysis",
]
